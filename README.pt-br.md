# KAIROS (καιρός)

### As verificações que um agente de código não consegue fazer sozinho

> **"A medida exata, no momento oportuno."**
>
> *kairos* é a palavra grega para o momento certo. O projeto honrou mal esse nome
> no primeiro ano. Veja a nota de retratação abaixo.

[![Licença: Apache-2.0](https://img.shields.io/badge/Licen%C3%A7a-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![Versão: 1.3.0](https://img.shields.io/badge/Vers%C3%A3o-1.3.0-blueviolet.svg)](plugin.json)

---

> ## ⚠️ Nota de retratação (2026-11-08)
>
> As versões até a v1.1.0 publicaram percentuais de economia de tokens, taxas de
> sucesso e resultados de "benchmark empírico" nesta página. **Aqueles números não
> eram medidos.** Eram constantes escritas dentro dos scripts de benchmark e
> impressas como se fossem observações.
>
> **Todos estão retirados.** Leia [`RETRACTION.md`](RETRACTION.md) para a lista
> completa, o mecanismo por trás de cada um e o que era de fato verdadeiro.

**Idiomas:** Português (Brasil, este arquivo) · [English](README.md)

---

## O que isto é

Quatro comandos fazem o que um modelo não consegue fazer raciocinando:

| Comando | Pergunta que responde | Por que o modelo não consegue |
| :--- | :--- | :--- |
| `kairos fit` | este ticket merece uma spec? | ele não conhece sua curva de custo medida |
| `kairos brainstorm` | o que rejeitamos, e o que provaria isto errado? | ele esquece a conversa que teve |
| `kairos gate` | o diff cumpre a spec aprovada? | a spec está fora do contexto dele |
| `kairos audit` | a mudança enfraqueceu algum teste? | isso é alegação, não observação |

`init` e `spec` são andaimes.

Ele não gera código, não chama modelo, não escolhe modelo. É a parte que se
recusa a aceitar a palavra do agente.

**A v1.3 removeu o resto.** O Dial Elástico, quatro personas de agente, nove
estágios de ciclo de vida, git worktrees, mutation testing, exportação para
harnesses, registro de extensões, lições no repositório e motor de
auto-atualização foram todos apagados. Nenhum tinha evidência por trás, e o
classificador em especial tomava decisões confiantes que não conseguia justificar.
Os dezesseis documentos deles estão em [`docs/archive/`](docs/archive/), não
apagados — apagar um documento que fez uma alegação é como a alegação desaparece.

`kairos scout` também saiu. Ele consultava npm, PyPI e crates para gaps de versão
ao vivo, o que era genuinamente útil, mas isso pertence a uma ferramenta de
dependências, não aqui. É recuperável do histórico do git na tag `pre-prune`.

---

## O ciclo

```bash
kairos fit --touches 4 --criteria 5      # isto merece uma spec?
kairos brainstorm --new dark_mode        # três alternativas e um falsificador
openspec propose dark-mode               # a spec (o OpenSpec cuida disso)
# ... implemente ...
kairos gate --spec openspec/changes/dark-mode/specs/ui/spec.md \
            --base main --verify "pytest -q"
```

Exit code é `0` só em READY, então entra num pre-push hook.

---

## O que o gate verifica

| Verificação | Veredito |
| :--- | :--- |
| Spec cobre menos de 6 das 8 seções medidas | **BLOCKED** |
| Um arquivo da lista de no-change foi modificado | **BLOCKED** |
| `--verify "<cmd>"` sai diferente de zero, ou estoura timeout | **BLOCKED** |
| Arquivos tocados que a spec nunca nomeou | REPAIR |
| Critérios de aceite sem teste no diff | REPAIR |
| Um debugger interativo (`breakpoint()`, `pdb`) adicionado | REPAIR |
| `git push`, `npm publish`, `terraform apply` adicionado | REPAIR — precisa de autorização |
| Deleção de teste ou teste enfraquecido | REPAIR |
| Uma dependência que a spec nunca mencionou | menor |
| Um arquivo novo 3x maior que todos os outros novos | menor |

Sem `--verify`, o relatório imprime `verification: NOT RUN — so 'tests pass' is a
claim`. Ele não insinua que os testes rodaram.

`brainstorm` recusa um brief com menos de três alternativas, com uma alternativa
sem motivo de rejeição, ou sem a seção "o que provaria isto errado". Uma spec sem
alternativas registradas não é uma decisão.

### O que ele não faz

- Compara **palavras, não significado**. Um teste nomeado como um critério mas que
  não afirma nada passa na checagem de drift.
- **Não roda seus testes** a menos que você passe `--verify`.
- Não distingue uma deleção intencional de uma fraudulenta.
- Três regras do scanner vêm **desligadas por padrão** (precisão medida 0–17%).
- Lê specs em português e inglês. Outros idiomas pontuam baixo, e isso é uma
  limitação do verificador, não um julgamento da spec.

---

## O histórico medido do scanner

Uma sonda independente com oito padrões de fraude detectou três contra a v1.1.0.
Em **370 pull requests reais já mergeados** de 12 projetos open-source, com 75
alertas adjudicados individualmente:

| Regra | Onda 1 | Onda 2 |
| :--- | ---: | ---: |
| `assert_deletion` | 71% | **100%** |
| `weakened_test_skip` | 89% | 67% |
| `silent_failure_empty_catch` | 17% | **0%** |
| `guard_removal` | **0%** | **0%** |
| `phantom_stub` | **0%** | **0%** |

O padrão não é sutil: as duas regras que **contam** coisas funcionam. As três que
**reconhecem uma forma** em uma linha não funcionam, porque a forma é ambígua sem
contexto estrutural.

Com o conjunto padrão, o scanner detecta **6 de 24 casos de fraude (25%)** no
próprio corpus, com zero falso positivo nos 19 casos limpos. Ele é preciso quando
dispara e dispara pouco. **Não é um gate de segurança.**

Detalhamento completo, incluindo o que foi descartado:
[`docs/EXTERNAL_VALIDATION.md`](docs/EXTERNAL_VALIDATION.md).

---

## Instalação

Requer Python 3.10+. Sem dependências.

```bash
git clone https://github.com/ismaelsoilet/kairos-framework
cd seu-projeto
python3 /caminho/para/kairos-framework/scripts/kairos_cli.py init
```

### Referência de comandos

```bash
kairos init                                    # cria .kairos/
kairos fit --touches N --criteria N [--crosses-boundary] [--changes-schema-or-api]
kairos brainstorm --new <nome> | --check <caminho>
kairos spec <nome>                             # spec de oito seções
kairos gate --spec <caminho> [--base main] [--verify "<cmd>"] [--json]
kairos audit [--base main] [--enable-rule NOME]
```

---

## Estrutura do repositório

```text
kairos-framework/
├── RETRACTION.md                  # o que foi alegado, por que estava errado
├── CLAIMS.md                      # toda alegação viva + seu artefato
├── scripts/
│   ├── kairos_cli.py              # a CLI
│   ├── kairos_gate.py             # verificação spec <-> diff
│   └── kairos_brainstorm.py       # alternativas antes do compromisso
├── tests/
│   ├── test_gate.py
│   ├── test_brainstorm.py
│   └── fixtures/fraud_corpus/     # diffs rotulados + veredito esperado
├── skills/kairos/SKILL.md         # o protocolo voltado ao agente
├── agents/kairos_critic.md        # revisor de contexto zero
├── rules/kairos-core.md           # as cinco leis de ferro
└── docs/
    ├── EVIDENCE.md                # leia primeiro: cada regra e sua fonte
    ├── EXTERNAL_VALIDATION.md     # 370 PRs, adjudicados
    ├── OPPORTUNITIES.md           # o que vale construir, o que não vale
    └── archive/                   # o ciclo v1.2, mantido como registro
```

---

## Documentação

- [`docs/EVIDENCE.md`](docs/EVIDENCE.md) — **leia primeiro.** Cada regra ligada a uma fonte, com as limitações dessa fonte, e o que não é tratado como evidência.
- [`docs/EXTERNAL_VALIDATION.md`](docs/EXTERNAL_VALIDATION.md) — 370 PRs reais, 75 alertas adjudicados, e quais regras sobreviveram.
- [`RETRACTION.md`](RETRACTION.md) — as alegações retiradas na v1.2 e o mecanismo por trás de cada uma.
- [`CLAIMS.md`](CLAIMS.md) — o livro-razão. Todo número precisa de uma linha com artefato.
- [`docs/OPPORTUNITIES.md`](docs/OPPORTUNITIES.md) — que partes disto vale construir para outros, e o que não vale.

Dezesseis documentos que descreviam o ciclo da v1.2 foram para
[`docs/archive/`](docs/archive/) quando esse ciclo foi removido na v1.3, incluindo
o estudo de caso da execução única do Gemini.

---

## É um back end, não um framework

Use **uma** ferramenta de spec do começo ao fim — o OpenSpec é a melhor escolha
medida (42/50 mergeados, 2,4% de drift, fase de spec mais rápida em 12 min). O
`kairos gate` fica atrás dele, e atrás dos layouts EGM, Spec Kit ou KAIROS
igualmente.

Ele não substitui sua ferramenta de spec e não afirma que o formato dele é
melhor: o benchmark não encontrou diferença significativa entre nenhum deles
(banda de ruído de ±10pp).

---

## Licença

Apache License 2.0 — ver [`LICENSE`](LICENSE).

Construído por Ismael Soilet, com assistência de IA. A assistência de IA escreveu
algumas das alegações que precisaram ser retratadas; a retratação foi escrita com
as mesmas ferramentas e conferida contra a saída observada.
