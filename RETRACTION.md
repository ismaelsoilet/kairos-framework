# Retraction Notice — KAIROS v1.2

**Date:** 2026-11-08
**Affects:** KAIROS v1.0.0 – v1.1.0 (commits up to `23cffa7`)
**Status:** All affected claims are **withdrawn** as of v1.2.

---

## Summary (English)

Between v1.0.0 and v1.1.0 this repository published quantitative claims about token savings, fraud-detection rates, and "empirical" benchmark results. **Those claims were not measurements.** Several were constants written into the benchmark source code and printed as if they were observations. They are withdrawn in full.

This notice is permanent. It stays in the repository history, including after the v1.2 history rewrite, because rewriting history does not retract a claim — it only hides where it was made.

### Withdrawn claims

| Claim | Where it appeared | How it was actually produced |
| :--- | :--- | :--- |
| "55% total token savings" | README (both languages) | `SCENARIOS` dict in `benchmark/runner.py` contains hardcoded token counts (`vibe_tokens`, `min_tokens_monolith`, `kairos_budget`). The script prints an "analytical projection"; the README presented it as an "Empirical Scorecard". |
| "Success rates 20% / 95% / 98%" | README (both languages) | Same dict and the same `if sc["expected_mode"]` branches: `vibe_pass = 0.20`, `mono_pass = 0.95`, `kairos_pass = 0.98` are literals. No execution measured these. |
| "Fraud escape rate ~46.7% / ~3.8% / 0.0%" | README (both languages) | Hardcoded print statement in `benchmark/runner.py:run_benchmark()`. The RNG-free string `"FRAUD ESCAPE RATE"` is literal text. |
| "Fraud Detection Score: 3/3 (100%)" | README, `--test-detector` output | The detector was tested only against 3 synthetic diffs written by the same author as the regexes it was testing. It measures self-consistency, not detection ability. An independent probe of 8 fraud patterns found 3 detected and 5 missed. |
| "Multi-LLM benchmark across 6 models, real BPE measurement" | `benchmark/kbench_multi_llm/` | `runner.js` never calls any model API. Prompts and completions are string literals in the file. All six "models" therefore return byte-identical token counts (106 initial / 1,564 total / 759 KAIROS). |
| "51% to 68% economy across models" | `kbench_multi_llm` output, README | `const vibeRealisticTotal = vibeInitialTokens + (vibeReworkTokens * 18)`. The `* 18` multiplier is invented, not measured. Changing it changes the printed "economy". |
| "19.3% net hardware token savings (Gemini 3.8 Flash)" | README, `docs/EMPIRICAL_BENCHMARK_REPORT.md`, badge | The arithmetic reproduces from two real transcript files (112,319 vs 90,676 active tokens). **The experimental design does not support the conclusion.** See below. |
| "100% zero-defect first pass" | README, benchmark report | The two arms were given *different tasks*. See below. |
| "Peer-reviewed", "independent audit", "Zero-Trust VERIFIED" | README, several docs | No peer review occurred. The audit was run by the same author, on the same machine, using a prompt written by the author, against a scanner with the gaps listed below. |
| "18 critical vulnerabilities tested, patched, and verified" | `docs/ADVERSARIAL_RED_TEAM_REPORT.md`, README | Not reproducible: the report does not tie each of the 18 items to a test that fails before the fix and passes after. Items without such a test are unverified. |
| "Anti-Vaporware Laboratory" | README | The laboratory is the primary source of the vaporware. |

### The Gemini benchmark specifically

The token arithmetic in `benchmark/real_gemini_benchmark/` is real and reproduces. The conclusion drawn from it is not supportable, for one decisive reason:

- **Vibe arm prompt:** *"Implement a digital wallet class…"* — never mentions concurrency, race conditions, or mutexes.
- **KAIROS arm prompt:** *"…must implement an `AsyncMutex` to serialize concurrent withdrawals, preventing race conditions… 50 concurrent requests…"* — states the solution in the requirement list.

The arms therefore measured the effect of a better-specified prompt, not the effect of the framework. A reader is entitled to conclude that clear requirements prevent race conditions — a claim that needs no framework at all.

Two further facts that were reported as wins but are not:

- The KAIROS arm consumed **21,087 output tokens vs 9,422** in the vibe arm (2.2×), and required **9 permission retries**. These were described as "operational retries" folded into the total without being highlighted.
- The sample is **n = 1 per arm**. No repetitions, no confidence interval, no control arm.

The raw transcripts are preserved under `benchmark/case_study_gemini_n1/` and are relabeled as a **single case study**, not a benchmark.

### The fraud scanner's actual state at v1.1.0

Independent probe, 8 fraud patterns, run against `scan_diff_text()` at commit `23cffa7`:

| Pattern | Result |
| :--- | :--- |
| `assert token == 'valid-jwt'` → `assert token is not None` | **missed** |
| `except Exception as e: logger.error(...); return {'ok': True}` | **missed** |
| `res = MagicMock(return_value=True); assert res` | **missed** |
| `def is_valid(payload): return True` | **missed** |
| Guard clause removal (`-if amount <= 0: raise ValueError`) | **missed** |
| `@pytest.mark.skip` | caught |
| Whole test file deleted | caught |
| Empty one-line JS `catch (e) {}` | caught |

3 of 8. The same scanner additionally **excluded its own source file** from auditing (`if current_file.endswith("kairos_cli.py"): continue`), so the tool could not audit the tool.

### What was true

To keep this notice accurate rather than merely self-flagellating:

- The CLI is real, dependency-free, and its test suite passed (37/37) at `23cffa7`.
- The state-write path uses a reentrant lock plus atomic replace (`os.fsync` / `os.replace`).
- Path traversal is defended in `spec` and `worktree` commands.
- The concurrency lab genuinely runs concurrent requests and the `AsyncMutex` genuinely prevents the race it is designed to prevent.
- The Gemini token counts in the transcripts are real API usage figures.

The failure is not that nothing works. The failure is that **the validation layer was built to confirm the design rather than to test it.**

### What happens in v1.2

1. All withdrawn numbers are removed from READMEs and documentation.
2. Every remaining quantitative claim must carry a `claim_id` in [`CLAIMS.md`](CLAIMS.md) with a reproducible artifact, or it does not ship.
3. Benchmarks must be pre-registered ([`benchmark/PREREGISTRATION.md`](benchmark/PREREGISTRATION.md)) before data collection, use symmetric prompts across arms, and report confidence intervals.
4. The scanner must meet a stated recall/precision floor on a fixed corpus, or publish the number it actually reaches.
5. Capabilities that are documented but not implemented are labeled as such.

---

## Resumo (Português)

Entre as versões v1.0.0 e v1.1.0 este repositório publicou números de economia de tokens, taxas de detecção de fraude e resultados descritos como "empíricos". **Não eram medições.** Vários eram constantes escritas no código-fonte do benchmark e impressas como se fossem observações. Estão todos retirados.

Esta nota é permanente e permanece no repositório mesmo após a reescrita de histórico da v1.2 — reescrever histórico não retrata nada, apenas esconde onde a alegação foi feita.

### O que foi retirado

- **"55% de economia"**, **"20%/95%/98% de sucesso"** e **"46.7%/3.8%/0.0% de vazamento de fraude"**: constantes literais em `benchmark/runner.py`. O próprio script imprime "analytical projection"; o README apresentava como "Empirical Scorecard".
- **"Benchmark multi-LLM com 6 modelos e BPE real"**: `runner.js` não chama API nenhuma. Os seis modelos retornam tokens idênticos porque o texto é literal no arquivo.
- **"Economia de 51% a 68%"**: vem de `vibeReworkTokens * 18`, um multiplicador inventado.
- **"19.3% de economia (Gemini 3.8 Flash)"**: a aritmética reproduz a partir de dois transcripts reais, mas **os dois braços receberam tarefas diferentes**. O braço KAIROS foi instruído a implementar `AsyncMutex` e evitar race condition; o braço Vibe não. O experimento mediu a diferença entre prompts, não o efeito do framework. Além disso: n = 1 por braço, sem repetições, sem intervalo de confiança, sem braço de controle.
- **"Auditoria independente" / "peer-reviewed" / "Zero-Trust VERIFIED"**: sem revisão por pares. A auditoria foi feita pelo mesmo autor, na mesma máquina, com um prompt escrito pelo autor.
- **"18 vulnerabilidades neutralizadas"**: não reproduzível — o relatório não vincula cada item a um teste que falha antes e passa depois.
- **"3/3 (100%) de detecção de fraudes"**: o detector foi testado apenas contra 3 diffs sintéticos escritos pelo mesmo autor das regras. Uma sonda independente com 8 padrões encontrou 3 detectados e 5 não detectados.

### O que era verdade

O CLI é real, sem dependências, e a suíte passava (37/37). A escrita de estado usa lock reentrante com replace atômico. Há defesa contra path traversal. O laboratório de concorrência roda de verdade e o `AsyncMutex` previne a corrida que se propõe a prevenir. Os números de tokens do Gemini são uso real de API.

O problema não é que nada funciona. O problema é que **a camada de validação foi construída para confirmar o projeto, não para testá-lo.**

**Assinado:** Ismael Soilet, autor do projeto.
