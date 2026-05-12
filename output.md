# Output Format

This file defines the required benchmark report format.

The master writes one report:

```text
runs/<run_id>/report.md
```

## report.md

`report.md` is the human-readable benchmark result.

It should be concise and should not include full harness logs.

Required structure and example:

```md
# Benchmark Report

run_id: 20260511_153012_123456
agent: codex
k: 3
total_tasks: 2
total_subagents: 6

## Summary

pass@1_success_rate: 1/2 = 0.500
pass@k_success_rate: 2/2 = 1.000
subagent_success_rate: 2/6 = 0.333
passed_tasks: 2
failed_tasks: 0

## Results

| task | subagent_id | result |
|---|---|---|
| simple_add | agent_1 | success |
| simple_add | agent_2 | failure |
| simple_add | agent_3 | failure |
| matmul | agent_1 | failure |
| matmul | agent_2 | success |
| matmul | agent_3 | failure |
```
