# Relatório de QA interno (antigo "Certificação SureForge")

> **Aviso de escopo:** este documento era intitulado "*Relatório Oficial de
> Certificação SureForge — `[ READY FOR PRODUCTION RELEASE ]` (Certificação
> Incondicional) — Nota Real Final: 9.4/10*".
>
> Nada disso era verdade. Não houve certificação, não houve organismo
> certificador, e a nota 9.4/10 foi atribuída pelo próprio autor ao próprio
> projeto. Uma nota que o autor se dá não é uma avaliação; é uma opinião com
> formato de métrica.
>
> O documento permanece como registro de QA interno, que é o que ele sempre foi.

---

## O que um QA interno pode afirmar

Executado na v1.2, sobre o código deste repositório:

| Verificação | Comando | Resultado |
| :--- | :--- | :--- |
| Suíte de testes passa | `python3 -m unittest tests/test_cli_features.py` | 39 testes, exit 0 |
| Scanner contra corpus rotulado | `python3 benchmark/eval_corpus.py` | recall 100%, precision 96% (1 falso positivo conhecido) |
| Scanner audita o próprio código | `python3 scripts/kairos_cli.py audit --base HEAD --root-only` | sim — a exclusão do próprio arquivo foi removida |
| Audit exige evidência de mutação | teste `test_audit_requires_mutation_evidence_before_verified` | sim — diff limpo sem K-Mutant resulta em `REPAIR` |
| Telemetria não é auto-declarada | `kairos token import --usage <log>` | sim — `token add` foi removido |
| Dial respeita override explícito | teste `test_dial_force_beta_overrides_gamma_keyword` | sim |

## O que este documento **não** afirma

- **Não afirma prontidão para produção.** Não há teste de carga, não há revisão
  de segurança por terceiro, não há auditoria de dependências.
- **Não atribui nota.** Nota numérica para software próprio sem critério externo
  é ruído.
- **Não certifica segurança.** A versão anterior deste relatório afirmava que
  "18 vulnerabilidades foram 100% neutralizadas". O relatório de red team não
  vincula cada item a um teste que falha antes e passa depois; sem essa ligação,
  o número não é verificável. Ver [`ADVERSARIAL_RED_TEAM_REPORT.md`](ADVERSARIAL_RED_TEAM_REPORT.md),
  reescrito com o mesmo critério.
- **Não compara com concorrentes.** Comparação sem executar o outro lado é
  opinião.

## O que seria necessário para uma certificação real

1. Auditor que não escreveu o código e não recebeu o roteiro.
2. Critérios publicados antes da auditoria, com casos negativos obrigatórios.
3. Ambiente limpo, sem estado prévio do autor.
4. Publicação integral dos achados, incluindo os que o autor preferia não ver.

Nada disso aconteceu aqui. O que existe é um projeto que passou na própria suíte
de testes e mediu o próprio scanner contra o próprio corpus. É útil saber disso.
Não é uma certificação.
