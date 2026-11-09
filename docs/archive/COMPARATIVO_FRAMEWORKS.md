# Comparação com outros frameworks — o que este documento pode e não pode afirmar

> **Aviso:** a versão anterior deste arquivo era uma matriz de 12 critérios
> atribuindo notas a sete projetos (Google EGM, OpenSpec, Superpowers, Fable,
> SureForge, Aider/Cursor), incluindo a linha "Economia de Tokens em UI:
> **85%–93%**" para o KAIROS contra "< 10%" para todos os outros.
>
> **Nenhum desses frameworks foi executado para produzir essa tabela.** As notas
> foram atribuídas lendo a documentação dos outros projetos e assumindo que o
> KAIROS se comportaria como pretendido. Uma comparação sem execução do outro
> lado é opinião formatada como dado — o mesmo defeito que gerou a retratação.

---

## O que dá para afirmar com honestidade

Diferenças de **escopo e mecanismo**, verificáveis lendo o código deste
repositório e a documentação pública dos outros. Sem notas, sem percentuais.

| Aspecto | KAIROS | O que os outros fazem (pela documentação deles) |
| :--- | :--- | :--- |
| **Camada de atuação** | Governança de processo + CLI de auditoria de diff | A maioria atua em uma camada só: spec (EGM, OpenSpec), execução (Aider/Cursor), ou revisão (Fable, SureForge) |
| **Classificação de risco** | Por palavra-chave no texto da tarefa. Simples, e erra (ver README) | Não é um problema que a maioria dos projetos declara resolver |
| **Isolamento** | `git worktree` com symlink automático de dependências | Superpowers usa scripts próprios; outros deixam a cargo do usuário |
| **Auditoria de diff** | Determinística, por regex e comparação de pares. **Recall medido: 100% no corpus interno, 75% em holdout limpo** | Fable-judge e SureForge são baseados em prompt de LLM, o que é uma abordagem diferente e não comparável sem execução |
| **Mutation testing** | Embutido (`kairos mutate`), 15 operadores | Não é recurso declarado pelos outros |
| **Dependências** | Zero. Python 3 puro, um arquivo | A maioria exige Node, plugin de IDE ou um harness específico |

## O que este documento **não** afirma

- **Não afirma que o KAIROS economiza mais tokens.** Nenhum número de economia
  foi medido. O protocolo para medir está em
  [`benchmark/PREREGISTRATION.md`](../benchmark/PREREGISTRATION.md) e não foi
  executado.
- **Não atribui nota a ninguém.** Nem ao KAIROS, nem aos outros.
- **Não afirma superioridade em qualidade.** Sem rodar os dois lados na mesma
  tarefa com juiz cego, não há base para isso.

## Como fazer essa comparação de verdade

1. Escolher 3 tarefas representativas (uma de UI, uma de lógica, uma de risco).
2. Rodar cada framework, com o mesmo modelo, n = 5.
3. Medir tokens ativos, defeitos encontrados por juiz cego, e tempo até entrega.
4. Publicar a tabela bruta e o intervalo de confiança.

Custo estimado: semanas de execução e orçamento de API. Não foi feito. Até ser
feito, este documento descreve mecanismos, não desempenho.

## Inspirações declaradas

O KAIROS não inventou a maior parte do que faz, e não reivindica isso:

- **Delta specs** — conceito de OpenSpec.
- **Crítico de contexto zero** — ideia do Goldfish / EGM.
- **TDD cirúrgico** — práticas de Superpowers e da literatura de TDD.
- **Auditoria adversarial de diff** — abordagem de Fable / SureForge.
- **Mutation testing** — técnica estabelecida, não originada aqui.

O que é específico deste projeto: a combinação, a CLI sem dependências, e o
classificador Elástico (que hoje é `grep` de palavra-chave, e está descrito como
tal no README).
