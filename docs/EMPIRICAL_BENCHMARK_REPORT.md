# Relatório: uma execução comparativa (n = 1 por braço) — **não é um benchmark**

> **Data:** 08 de novembro de 2026
> **Versão avaliada:** KAIROS v1.1.0
> **Veredito deste documento:** os números de tokens são reais; **a conclusão que
> foi publicada a partir deles não se sustenta.**
>
> Este arquivo substitui a versão anterior, intitulada "Benchmark Científico,
> Telemetria de Hardware e Auditoria Adversarial Independente". O título anterior
> continha três afirmações falsas: não era científico (sem pré-registro, sem
> repetição, sem braço de controle), não era benchmark (n = 1), e não era
> independente (mesmo autor, mesma máquina, prompt do autor).
>
> Ver [`RETRACTION.md`](../RETRACTION.md). Estudo de caso completo em
> [`case-studies/GEMINI_N1.md`](case-studies/GEMINI_N1.md).

---

## O que foi feito

Duas sessões de agente no mesmo modelo, no mesmo dia:

- **Braço A (livre):** recebeu *"implemente uma classe de carteira digital com
  `withdraw` e `applyPromo`"*. O enunciado não menciona concorrência.
- **Braço B (governado):** recebeu a mesma tarefa **mais** a instrução de
  implementar `AsyncMutex` para serializar saques, prevenir race conditions, e
  testar com 50 requisições concorrentes.

## Por que isso não mede o framework

Os dois braços não receberam a mesma tarefa. O braço governado recebeu a solução
no enunciado. Portanto a diferença observada é compatível com uma explicação que
não envolve KAIROS em absoluto: **um requisito bem escrito evita o defeito**.

Some-se a isso:

- **n = 1 por braço.** Sem repetição, sem intervalo de confiança.
- **Sem braço de controle.** Não há como separar "aviso sobre o perigo" de
  "processo de governança".
- **O braço governado gastou 2,2× mais tokens de saída** (21.087 vs 9.422) e
  precisou de **9 retentativas de permissão**. Esses fatos foram apresentados
  antes como "retentativas operacionais" e não apareciam no destaque.

## O que reproduz de fato

Os números de tokens vêm de `usage` real da API, preservados nos transcripts, e a
aritmética reproduz:

| Métrica | Braço livre | Braço governado |
| :--- | ---: | ---: |
| Input | 102.897 | 69.589 |
| Output | 9.422 | 21.087 |
| **Ativos (in+out)** | **112.319** | **90.676** |
| Cache read | 500.762 | 319.139 |

Comando: `python3 benchmark/case_study_gemini_n1/run_real_gemini_benchmark.py`.

O laboratório de concorrência também reproduz e é independente da justiça dos
prompts:

- implementação do braço livre: 60 saques concorrentes de R$ 10 sobre R$ 500 →
  60 sucessos, saldo final **−R$ 100**;
- a mesma implementação após o ciclo de reparo → 50 sucessos, 10 rejeições,
  saldo 0;
- implementação do braço governado → 50 sucessos, 10 rejeições, saldo 0, na
  primeira passagem.

Isso demonstra que **o mutex funciona**. Não demonstra que o framework faz um
agente chegar ao mutex com mais frequência do que um requisito claro chegaria.

## O que foi retirado deste documento

| Alegação anterior | Motivo |
| :--- | :--- |
| "19,3% de economia líquida de tokens" | diferença real entre braços desiguais; não é efeito do framework |
| "100% zero-defeito na primeira passagem" | consequência direta da assimetria de enunciado |
| "33,15% de economia com cache read" | mesmo cálculo, denominador diferente, comparação não like-for-like |
| "Auditoria Adversarial Independente / VERIFIED 6/6" | mesmo autor, mesma máquina, prompt do autor; o scanner usado tinha 5 lacunas conhecidas de detecção |
| "peer-reviewed" | não houve revisão por pares |

## O que faria disso um experimento

Está escrito, antes da coleta de dados, em
[`benchmark/PREREGISTRATION.md`](../benchmark/PREREGISTRATION.md): três braços
(livre, aviso, governado) com o mesmo texto de tarefa, n = 5, ordem randomizada,
IC95% por bootstrap, juiz cego para qualidade, e a regra de decisão fixada de
antemão — se o intervalo incluir zero, a conclusão publicada é "não demonstrado".

Nenhuma execução desse protocolo foi feita. Não há credenciais nem orçamento
autorizado neste ambiente.

---

## Como ler este documento

Se você quer saber **se o mutex funciona**: sim, e há código executável aqui.
Se você quer saber **se o KAIROS economiza tokens**: não se sabe. O único número
que existia foi produzido comparando duas tarefas diferentes, e foi retirado.
