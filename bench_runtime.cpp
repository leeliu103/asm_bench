#include <hip/hip_runtime.h>

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

static hipModule_t module = NULL;
static hipFunction_t function = NULL;
static int initialized = 0;
static int loaded = 0;

static int check_hip(hipError_t err, const char *what) {
    if (err == hipSuccess) return 0;
    fprintf(stderr, "bench_runtime: %s failed: %s\n", what, hipGetErrorString(err));
    return -1;
}

extern "C" int bench_init(void) {
    if (initialized) return 0;

    if (check_hip(hipInit(0), "hipInit") != 0) return -1;
    if (check_hip(hipSetDevice(0), "hipSetDevice") != 0) return -1;

    hipDeviceProp_t props;
    if (check_hip(hipGetDeviceProperties(&props, 0), "hipGetDeviceProperties") != 0) {
        return -1;
    }
    fprintf(stderr, "bench_runtime: GPU %s (%s)\n", props.name, props.gcnArchName);

    initialized = 1;
    return 0;
}

extern "C" int bench_load(const char *hsaco_path, const char *kernel_name) {
    if (!initialized) {
        fprintf(stderr, "bench_runtime: call bench_init before bench_load\n");
        return -1;
    }

    if (loaded) {
        (void)hipModuleUnload(module);
        module = NULL;
        function = NULL;
        loaded = 0;
    }

    hipError_t err = hipModuleLoad(&module, hsaco_path);
    if (err != hipSuccess) {
        fprintf(stderr, "bench_runtime: hipModuleLoad(%s) failed: %s\n",
                hsaco_path, hipGetErrorString(err));
        return -1;
    }

    err = hipModuleGetFunction(&function, module, kernel_name);
    if (err != hipSuccess) {
        fprintf(stderr, "bench_runtime: hipModuleGetFunction(%s) failed: %s\n",
                kernel_name, hipGetErrorString(err));
        (void)hipModuleUnload(module);
        module = NULL;
        function = NULL;
        return -1;
    }

    loaded = 1;
    return 0;
}

extern "C" int bench_launch(uint32_t grid_x,
                             uint32_t grid_y,
                             uint32_t grid_z,
                             uint32_t block_x,
                             uint32_t block_y,
                             uint32_t block_z,
                             uint32_t shared_mem_bytes,
                             const void *kernargs,
                             size_t kernargs_size) {
    if (!loaded) {
        fprintf(stderr, "bench_runtime: call bench_load before bench_launch\n");
        return -1;
    }

    size_t arg_size = kernargs_size;
    void *extra[] = {
        HIP_LAUNCH_PARAM_BUFFER_POINTER, (void *)kernargs,
        HIP_LAUNCH_PARAM_BUFFER_SIZE, &arg_size,
        HIP_LAUNCH_PARAM_END
    };

    hipError_t err = hipModuleLaunchKernel(
        function,
        grid_x, grid_y, grid_z,
        block_x, block_y, block_z,
        shared_mem_bytes,
        0,
        NULL,
        extra
    );

    return check_hip(err, "hipModuleLaunchKernel");
}

extern "C" int bench_sync(void) {
    return check_hip(hipDeviceSynchronize(), "hipDeviceSynchronize");
}

extern "C" void bench_shutdown(void) {
    if (module) (void)hipModuleUnload(module);
    module = NULL;
    function = NULL;
    loaded = 0;
    initialized = 0;
}
