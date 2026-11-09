# KAIROS (καιρός)

### Uma camada de governança de processo para agentes de código — specs, TDD, mutation testing e auditoria de diff

> **"A medida exata, no momento oportuno."**
>
> Sobre o nome: *kairos* é a palavra grega para o momento certo, em oposição a *chronos*, mero tempo decorrido. O projeto honrou mal esse nome no primeiro ano. Veja abaixo.

[![Licença: Apache-2.0](https://img.shields.io/badge/Licen%C3%A7a-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![Versão: 1.2.0](https://img.shields.io/badge/Vers%C3%A3o-1.2.0-blueviolet.svg)](plugin.json)

---

> ## ⚠️ Nota de retratação (2026-11-08)
>
> As versões até a v1.1.0 publicaram percentuais de economia de tokens, taxas de sucesso e resultados de "benchmark empírico" nesta página. **Aqueles números não eram medidos.** Eram constantes escritas dentro dos scripts de benchmark e impressas como se fossem observações.
>
> **Todos estão retirados.** Leia [`RETRACTION.md`](RETRACTION.md) para a lista completa, o mecanismo por trás de cada um e o que era de fato verdadeiro.
>
> Este README não contém mais nenhuma alegação quantitativa de desempenho, porque nenhuma atualmente atende ao padrão de evidência que o projeto exige de terceiros. Alegações podem voltar quando carregarem um artefato reproduzível — ver [`CLAIMS.md`](CLAIMS.md).

**Idiomas:** Português (Brasil, este arquivo) · [English](README.md)

---

## O que o KAIROS é

O KAIROS é um conjunto de convenções mais uma CLI em Python sem dependências que impõe um processo disciplinado a um agente de código:

- classificar o risco da tarefa antes de trabalhar
- escrever uma delta spec antes de escrever código
- implementar dentro de um `git worktree` isolado
- escrever o teste que falha primeiro
- mutar a implementação e confirmar que os testes a capturam
- varrer o `git diff` resultante em busca de sinais de que o agente trapaceou
- arquivar a spec e registrar a lição

Ele não gera código. Não chama modelo. Não tem opinião sobre qual modelo você usa. É a parte que se recusa a aceitar a palavra do agente.

Tudo abaixo está implementado em `scripts/kairos_cli.py` ou marcado como não implementado. Essa distinção é o ponto da v1.2.

---

## Status das capacidades

Camadas honestas. Se a capacidade está na terceira coluna, não planeje em cima dela.

### Implementado e coberto por testes

| Capacidade | Comando | Evidência de teste |
| :--- | :--- | :--- |
| Estado do projeto, escrita atômica, lock reentrante | `init`, `status` | `atomic_state_save`, `state_file_locking_context_manager` |
| Classificação de risco (por palavra-chave) | `dial` | `dial_security_and_financial_prioritization` |
| Scaffold de delta spec (5 arquivos) | `spec` | `spec_name_sanitization_rejects_path_traversal` |
| Varredura de fraude no diff | `audit` | 15 testes de scanner (positivos e negativos) |
| Reconhecimento de manifestos | `scout` | `scout_detects_cutoff_risk_packages`, `scout_cli_execution` |
| Descoberta de skills e agentes | `registry` | `registry_discovers_agents_and_skills` |
| Lições no repositório | `lesson add/list` | `lesson_add_and_list` |

### Implementado, sem teste

`worktree create/remove/list`, `archive`, `export`, `rollback`, o motor `mutate` de ponta a ponta (só a tabela de operadores é verificada) e a renderização de `status --dashboard`. Listados aqui de propósito: um comando sair com código 0 não é evidência de que funciona.

### Documentado, não implementado

- **`kairos drift`** — citado por `skills/kairos-sync/SKILL.md` e `docs/AGENT_LESSONS.md`. O subcomando não existe. Removido da documentação na v1.2 até ser implementado ou removido de vez.
- **Aplicação de blast radius** — `docs/ARCHITECTURE.md` afirmava que o scanner comparava os arquivos tocados com os caminhos declarados em `tasks.md`. Não compara. Scope creep é responsabilidade de revisão, não recurso do scanner, até ser implementado.
- **`invoke_subagent(...)`** — aparece como código em duas skills. É um primitivo do harness, não fornecido por este repositório. As skills agora dizem isso explicitamente.

---

## As cinco leis de ferro

De [`rules/kairos-core.md`](rules/kairos-core.md):

1. **Nenhum código de produção sem um teste que falha.** Se você não viu o teste falhar, você não sabe o que ele testa.
2. **Nenhum chute na depuração.** Reproduza o defeito em um teste mínimo antes de tocar no código de produção.
3. **A verdade é o `git diff`.** Alegações não são evidência. Saída de comando e inspeção de diff são.
4. **Cace as seis fraudes clássicas** — checks enfraquecidos, conclusão falsa, scope creep, ação não autorizada, traição de spec, debris.
5. **Especificações vivas.** Trabalho concluído arquiva sua spec em `.kairos/specs/`.

A lei 3 é a que este projeto violou mais profundamente, e a razão da retratação no topo desta página.

---

## O Dial Elástico

Três profundidades de processo, escolhidas pelo classificador em `dial`:

| Modo | Indicado para | Pipeline | Subagentes | Alvo de orçamento |
| :--- | :--- | :--- | :--- | :--- |
| **Alpha** | UI, texto, layout, CSS, edições pequenas | micro-delta na mesma conversa, edição cirúrgica, checagem de sanidade do diff | 0 | pequeno |
| **Beta** | novo endpoint, mudança de lógica, bugfix | recon → delta spec → worktree → TDD estrito → varredura de diff | 1 | médio |
| **Gamma** | auth, pagamentos, migrações, lógica central | recon → spec + crítico de contexto zero → worktree → TDD → mutation testing → auditoria adversarial | até 3 | grande |

**Limitação conhecida, dita sem rodeio:** a classificação é casamento de palavras-chave sobre a descrição da tarefa (`ALPHA_KEYWORDS` / `GAMMA_KEYWORDS` em `kairos_cli.py`). Ela não sabe quais arquivos você vai tocar, qual o tamanho do diff, nem se a área tem cobertura de teste. Consequências:

- Um ajuste de CSS que mencione "balance" classifica como **Gamma**.
- `--force-beta` não sobrepõe uma palavra-chave Gamma (correção em andamento).
- Os números de orçamento são alvos de planejamento, não medições. O KAIROS não mede seu consumo de tokens. Ver "Telemetria".

Um roteador de risco baseado em sinais objetivos — caminhos alterados, tamanho do diff, cobertura de teste da área, histórico de incidentes — é a versão honesta dessa ideia e ainda não está construído. Ver [`docs/OPPORTUNITIES.md`](docs/OPPORTUNITIES.md).

---

## As quatro personas

| Agente | Papel | O que ele realmente faz |
| :--- | :--- | :--- |
| `kairos_scout` | Technology Scout | Lê manifestos de dependência e sinaliza pacotes com histórico de quebra de API. Nada além disso. |
| `kairos_critic` | Crítico Goldfish | Revisa uma spec sem contexto de conversa, para não ser convencido a concordar. |
| `kairos_worker` | Executor Cirúrgico | TDD dentro de uma worktree; toca apenas os arquivos declarados. |
| `kairos_auditor` | Auditor de Diff | Reexecuta comandos, inspeciona o diff, reporta evidência. O veredito dele vale o que vale o scanner — leia as limitações abaixo antes de confiar. |

---

## O que o scanner realmente pega

`scan_diff_text()` roda expressões regulares sobre as linhas adicionadas de um `git diff`. Ele captura de forma confiável as formas **literais** de:

- testes pulados, focados ou comentados (`test.skip`, `xit`, `@pytest.mark.skip`, `// assert ...`)
- handlers de exceção vazios ou engolidos (`except: pass`, `catch (e) {}`)
- stubs retornando constantes triviais (`def f(): pass`, `return null;`)
- asserções tautológicas (`assert True`, `assert 1 == 1`, `expect(true).toBeTruthy()`)
- deleção líquida de asserções ou de funções de teste
- identificadores de modelo obsoletos em código

Ele **não** pega, a partir da v1.2:

- uma asserção enfraquecida no lugar (`assert x == 'valid'` → `assert x is not None`)
- um handler que registra o erro e então retorna sucesso
- um mock substituindo a unidade sob teste
- uma função de validação que retorna `True` incondicionalmente
- uma guarda removida

Uma sonda independente com oito padrões de fraude detectou três. O corpus em `tests/fixtures/fraud_corpus/` existe para tornar esse número mensurável e para subi-lo; o recall e a precision medidos atualmente estão em [`CLAIMS.md`](CLAIMS.md) — o que a execução do corpus reportar, não uma meta reescrita como resultado.

**O scanner não exclui mais o próprio arquivo-fonte da auditoria.** Até a v1.1.0 ele excluía (`if current_file.endswith("kairos_cli.py"): continue`), o que significava que a ferramenta não conseguia auditar a ferramenta. Essa exclusão foi removida.

---

## Telemetria: o que ela mede e o que não mede

A linha de status é assim:

```text
⚡ [KAIROS | Stage: BUILDING | Mode: BETA | Budget: 65,000 | Spent: UNMEASURED]
```

`Stage` e `Mode` vêm de `.kairos/state.json`. `Budget` é um alvo de planejamento.

`Spent` é **`UNMEASURED`** até você importar dados reais de uso com `kairos token import --usage <log.jsonl>`, que lê contagens reais de tokens de input/output/cache e custo de um log de harness, e registra o hash do arquivo-fonte junto. Até a v1.1.0 o campo era preenchido por `kairos token add <n>` — o agente incrementando o próprio contador, que é exatamente o modo de falha que este projeto diz detectar. Esse comando foi removido.

Se nada foi medido, o status diz isso. Não imprime zero para você inferir que zero tokens foram gastos.

---

## Instalação e primeiro uso

Requer Python 3.10+. Sem dependências.

```bash
git clone https://github.com/ismaelsoilet/kairos-framework
cd seu-projeto
python3 /caminho/para/kairos-framework/scripts/kairos_cli.py init
python3 /caminho/para/kairos-framework/scripts/kairos_cli.py dial "adicionar retry no webhook de pagamento"
```

### Referência de comandos

```bash
kairos init                                     # cria .kairos/ e state.json
kairos dial "<tarefa>" [--force-alpha|--force-beta|--force-gamma]
kairos scout [--all] [--save-spec]              # reconhecimento de manifestos
kairos spec <nome>                              # delta spec de 5 arquivos
kairos worktree create|remove|list <nome>
kairos mutate <arquivo> --test "<cmd>" [--max-mutants N] [--timeout S]
kairos audit --base main [--worktree PATH|--root-only]
kairos archive <change_id>
kairos rollback [--worktree PATH|--root-only]
kairos status [--dashboard|--header-only]
kairos token import --usage <log.jsonl>
kairos lesson add|list
kairos registry
kairos export <claude|cursor|agents|universal|all>
kairos update [--skip-self-test]
```

---

## Estrutura do repositório

```text
kairos-framework/
├── RETRACTION.md              # o que foi alegado, por que estava errado
├── CLAIMS.md                  # toda alegação quantitativa viva + artefato
├── rules/kairos-core.md       # diretrizes e as cinco leis de ferro
├── agents/                    # personas scout, critic, worker, auditor
├── skills/                    # 7 skills de protocolo (dial, spec, build, judge, …)
├── scripts/kairos_cli.py      # a CLI sem dependências
├── tests/
│   └── fixtures/fraud_corpus/ # diffs rotulados (fraude vs limpo) + veredito esperado
├── benchmark/
│   ├── PREREGISTRATION.md     # escrito antes da coleta de dados
│   └── case_study_gemini_n1/  # uma execução real, reclassificada como estudo de caso
└── docs/                      # arquitetura, lições, oportunidades
```

---

## Documentação

- [`RETRACTION.md`](RETRACTION.md) — as alegações retiradas e o mecanismo por trás de cada uma.
- [`CLAIMS.md`](CLAIMS.md) — o livro-razão. Todo número neste repositório precisa de uma linha.
- [`docs/OPPORTUNITIES.md`](docs/OPPORTUNITIES.md) — que partes disto vale construir para outras pessoas, e o que não vale.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — como as peças se encaixam.
- [`docs/AGENT_LESSONS.md`](docs/AGENT_LESSONS.md) — heurísticas de comportamento, sem alegações de desempenho.
- [`docs/case-studies/GEMINI_N1.md`](docs/case-studies/GEMINI_N1.md) — uma execução, os dois braços, incluindo a falha de desenho.

---

## Licença

Apache License 2.0 — ver [`LICENSE`](LICENSE).

Construído por Ismael Soilet, com assistência de IA. A assistência de IA escreveu algumas das alegações que precisaram ser retratadas; a retratação foi escrita com as mesmas ferramentas e conferida contra a saída observada.
