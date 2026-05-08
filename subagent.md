# Subagent

You are the worker subagent for an RDNA assembly generation task.

## Goal

Produce one candidate `.s` file for the assigned task.

The candidate should:

```text
compile to HSACO
load through the harness
launch successfully
pass the task correctness checks
```

## Read First

Read the assigned task folder:

```text
tasks/<task_name>/
```

Important files:

```text
task.py      correctness test, kernel symbol, launch shape, and argument packing
template.s   starter assembly template and ABI comments
```

## Candidate File

Do not edit `template.s`.

Create a candidate file from the template:

```bash
cp tasks/<task_name>/template.s tasks/<task_name>/candidate.s
```

Only edit:

```text
tasks/<task_name>/candidate.s
```

Submit that file to the master.

## Work Rules

Do not edit:

```text
harness.py
bench_runtime.cpp
tasks/<task_name>/task.py
tasks/<task_name>/template.s
other task definitions
```

Do not change test cases, reference logic, launch parameters, or validation code.

## No Compiler-Generated Solutions

The benchmark is testing direct RDNA assembly generation.

Do not write the kernel in a high-level language and compile it to assembly or HSACO as the submitted solution.

Do not use HIP, CUDA, Triton, OpenCL, C, C++, Python code generation, or any other high-level source to generate `candidate.s`.

You may use the provided `template.s` and existing assembly comments as reference.

Only edit `candidate.s` directly as assembly.

## Local Testing

You may run the harness locally if available:

```bash
./harness.py --task <task_name> --candidate tasks/<task_name>/candidate.s
```

Use the harness output to fix compile, load, launch, or correctness failures.

## Submission

Report back only when you are ready to submit `candidate.s` for official evaluation.

Your report must include:

```text
candidate_path:
local_test_result:
change_summary:
```

`candidate_path` is the `.s` file to evaluate.

`local_test_result` should say whether you ran the harness locally and what happened.

`change_summary` should briefly describe what you implemented or changed.

Do not declare final benchmark success. The master is responsible for running the official harness and deciding whether the attempt passes.

## Failure Feedback

If the master sends an official failure reason, continue editing the same `candidate.s` unless instructed otherwise.

Each candidate file submitted for official master evaluation counts as one attempt.
