# Red team: o que foi testado, o que foi corrigido, e o que não está provado

> **Data original:** 07 de novembro de 2026
> **Reescrito em:** 08 de novembro de 2026, durante a v1.2
>
> **Aviso:** a versão anterior afirmava que "todas as 18 vulnerabilidades foram
> reproduzidas via TDD (Red) e 100% neutralizadas (Green)".
>
> Uma verificação item por item, feita durante a v1.2, encontrou **13 dos 20 itens
> com um teste correspondente**. Os outros 7 foram corrigidos no código, mas sem
> teste que prove a correção. A palavra "todas" não era verdadeira.

---

## Método desta reescrita

Para cada item do inventário original, procurei em `tests/test_cli_features.py`
um teste capaz de falhar se a correção fosse revertida. O critério não é "existe
código que trata isso", é "existe um teste que fica vermelho sem a correção".

Resultado: **13 com teste, 7 sem.** Os sete estão listados abaixo com o que
faltaria para fechar a lacuna.

---

## Itens com teste correspondente

| ID | Defeito | Teste |
| :--- | :--- | :--- |
| DEF-01 | Comentário entre `except:` e `pass` evadia o scanner | `test_diff_scanner_catches_comment_separated_empty_catch` |
| CRIT-01.2a | `catch (err) { }` multilinha invisível | `test_diff_scanner_catches_multiline_js_empty_catch` |
| CRIT-01.2b | `catch { }` (ES2019) invisível | `test_diff_scanner_catches_es2019_optional_catch_binding` |
| CRIT-01.3 | Refatoração legítima de assert virava falso positivo | `test_diff_scanner_prevents_false_positive_on_assert_refactoring` |
| DEF-02 | Stubs retornando `None`/`{}`/`[]`/`""` passavam | `test_diff_scanner_catches_stubs_returning_trivial_constants` |
| CRIT-02.1 | Regex de mutação inerte em código com espaço (`a == b`) | `test_mutation_operators_match_pep8_spaced_operators` |
| RISK-02 | `state.json` truncado em escrita não atômica | `test_atomic_state_save` |
| DEF-R2-01 | Path traversal em `spec`/`worktree` | `test_spec_name_sanitization_rejects_path_traversal` |
| DEF-R2-04 | `it.only` / `describe.only` desativando a suíte | `test_diff_scanner_catches_focused_tests_dot_only` |
| DEF-R2-05 | `pytest.xfail` mascarando quebra | `test_diff_scanner_catches_pytest_xfail` |
| DEF-R2-07 | Arquivo de teste apagado inteiro (`+++ /dev/null`) | `test_diff_scanner_catches_completely_deleted_test_files` |
| DEF-R2-08 | `assert True` / `assert 1 == 1` substituindo asserção real | `test_diff_scanner_catches_tautological_assert_laundering` |
| DEF-R2-09 | Mutações JS/TS (`true`/`false`, `===`, `&&`) ausentes | `test_mutation_operators_support_js_ts_operators` |

## Itens corrigidos sem teste — lacuna declarada

| ID | Defeito | Correção aplicada | O que falta |
| :--- | :--- | :--- | :--- |
| CRIT-02.2 | Interrupção no meio da mutação deixava o código corrompido | `try/finally` que restaura o backup | Teste que mate o processo no meio e verifique a restauração |
| CRIT-03 | `runner.py` imprimia constantes como se fossem medição | O cabeçalho agora diz "analytical projection" | Nenhum teste pode provar que um número é honesto — só remover o número, como foi feito |
| SIMPL-01 | Worktree sem `.venv`/`node_modules` quebrava os testes | Symlinks automáticos | Teste de integração que crie worktree e rode a suíte |
| SIMPL-02 | `rollback` descartava estado sem backup | Gera `.patch` antes do `reset --hard` | Teste que suje o worktree, rode rollback e verifique o patch |
| DEF-R2-02 | Mutante em loop infinito travava o harness | `timeout=15s` | Teste com mutante que trava de propósito |
| DEF-R2-03 | `token add -N` subtraía tokens | **Comando removido** — `token import` é o substituto | Coberto pelos testes novos de import |
| DEF-R2-06 | Deleção de `def test_...` sem tocar no assert | Balanço líquido de funções de teste | Teste unitário do balanço |

Nenhum destes sete é uma falha grave em produção hoje. O problema era a palavra
"todas".

---

## O que a v1.2 acrescentou

Um item que não estava no inventário original, encontrado durante a auditoria
independente que gerou a retratação:

| ID | Defeito | Estado |
| :--- | :--- | :--- |
| **NEW-01** | O scanner excluía `scripts/kairos_cli.py` da própria análise (`if current_file.endswith("kairos_cli.py"): continue`) | Removido. Exclusão agora exige `--allow-file` explícito e é impressa no relatório |
| **NEW-02** | Cinco padrões de fraude reais passavam: assert enfraquecido, catch que loga e retorna sucesso, mock no alvo, validador incondicional, guarda removida | Implementados, com corpus rotulado em `tests/fixtures/fraud_corpus/` |

O NEW-01 é o mais relevante: enquanto ele existiu, o KAIROS não podia auditar a
si mesmo, e portanto o dogfooding era cerimônia.

---

## Como ler este relatório

- **13 itens** têm teste que falha sem a correção. São verificáveis.
- **7 itens** foram corrigidos no código sem prova automatizada. Confie neles
  como confiaria em qualquer código sem teste.
- **20 itens** é o inventário original. Ele não é "18", e não são "todos
  neutralizados".

Nenhum item aqui foi validado por terceiro. Não há CVE atribuído, não houve
auditoria externa paga. É um registro de QA interno, e é assim que deve ser lido.
