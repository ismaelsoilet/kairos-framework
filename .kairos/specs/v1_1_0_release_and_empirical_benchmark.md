# Behavioral Specifications: KAIROS v1.1.0

## Added Capabilities
- `kairos audit`: Writes `.kairos/audit_latest.json` with timestamp, verdict, and violations.
- `kairos mutate`: Writes `.kairos/kmutant_latest.json` with timestamp, score, killed/survived count.
- Multi-LLM testbed (`benchmark/kbench_multi_llm/`): Evaluates token consumption and concurrency robustness across models.

## Modified Capabilities
- `scan_diff_text`: Checks `is_code` on multiline statement inspection to avoid false positive matches in JSON or documentation files.
- Version string bumped from `1.0.0` to `1.1.0`.
