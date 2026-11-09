# Oportunidades reais — e o que não é

Avaliação do que, neste repositório, tem valor para outras pessoas. Critério único:
**quem paga, por quê, e o que teria que ser verdade para isso acontecer.**

Nada aqui é uma promessa. Cada item lista o que precisa ser demonstrado antes de
virar produto, e qual é o risco honesto.

---

## A. Scanner de fraude em código gerado por IA, rodando no CI

**O que é:** um binário que roda em `pre-commit` ou GitHub Action sobre o diff do
PR e falha quando detecta teste afrouxado, catch silencioso, stub fantasma, mock
no lugar da unidade sob teste, guarda removida ou asserção tautológica.

**Por que pode ter valor:** é o pedaço mais independente do projeto. Não exige
adotar SDLC, personas ou worktrees — só um comando no CI. O problema é real e
crescente: revisar código gerado por agente é diferente de revisar código humano,
e o modo de falha mais comum não é bug de sintaxe, é *verificação que não verifica*.

**O que teria que ser verdade:**

| Requisito | Estado atual |
| :--- | :--- |
| Recall e precision medidos num corpus fixo | corpus de 43 casos, recall 100% / precision 96% — **mas o corpus foi iterado contra as regras** |
| Generalização em dados não vistos | holdout limpo deu **6/8** antes de duas correções; depois disso não houve novo holdout |
| Tempo de execução aceitável (< 2s num diff de 500 linhas) | **não medido** |
| Falsos positivos toleráveis num PR real | 1 conhecido (mock de dependência externa indistinguível de mock do alvo) |

**Risco honesto:** lint e SAST já existem; o diferencial é o alvo específico, não
a tecnologia. E a maior fraqueza é a mesma que gerou a retratação: o corpus é meu.
Um produto real precisa de diffs vindos de PRs reais, com julgamento de terceiros.

**Próximo passo, se você quiser validar:** rodar o scanner sobre o histórico de PRs
de 3–5 repositórios open-source conhecidos, marcar manualmente os achados como
verdadeiro/falso positivo, e publicar a matriz de confusão. Custo baixo, e é o que
separa "tem um corpus" de "tem evidência".

---

## B. Ser quem mede honestamente num campo cheio de hype

**O que é:** executar o protocolo de `benchmark/PREREGISTRATION.md` e publicar o
resultado, positivo ou negativo, com IC95% e tabela bruta por execução.

**Por que pode ter valor:** praticamente ninguém no espaço de "agentic SDLC"
publica pré-registro e intervalo de confiança. Os números que circulam são
majoritariamente projeções — inclusive os que este projeto publicou.

**O que teria que ser verdade:** os resultados são publicados independentemente de
favorecerem o KAIROS. Se o braço governado custar mais, isso é o resultado.

**Quem se beneficia:** você, como autoridade técnica; e o campo, que ganha um dado
utilizável. Não é produto.

**Risco:** o resultado pode ser "não demonstrado" ou "KAIROS custa mais". Ambos são
publicáveis e ambos valem mais que um número inventado.

**Bloqueio atual:** sem credenciais de API e sem teto de gasto autorizado. Custo
mínimo do desenho: 30 ciclos de agente (3 braços × 5 repetições × 2 tarefas).

---

## C. O Dial Elástico feito de verdade (roteador de risco)

**O que é:** hoje o classificador é `sum(palavra-chave)`. Um fix de CSS que mencione
"balance" vira Gamma. A versão honesta decide profundidade de processo por sinais
objetivos: arquivos tocados, tamanho do diff, se o path é crítico (auth, pagamento,
migração), cobertura de teste da área, histórico de incidentes.

**Por que pode ter valor:** qualquer time com custo de inferência alto precisa
decidir quanto processo aplicar. É um problema de roteamento, não de prompt.

**O que teria que ser verdade:** o roteador prevê risco melhor que "sempre Gamma" e
melhor que aleatório. Isso é mensurável — curva de calibração, comparando a
classificação prevista com o que de fato exigiu retrabalho.

**Risco:** sem histórico de incidentes real, não existe alvo para calibrar. Sem
isso, o roteador é opinião com passos extras — que é o que ele é hoje.

---

## O que **não** é oportunidade

Registrado para não repetir o erro, não para desanimar.

- **"Framework de SDLC completo que substitui o processo de engenharia."** Nada
  aqui sustenta isso. O que existe é um CLI de governança com detecção parcial.
- **Qualquer alegação de segurança** ("impenetrável", "18 vulnerabilidades
  neutralizadas") sem CVE, sem auditoria paga, sem teste que falha antes e passa
  depois por item.
- **Benchmark de si mesmo.** Foi o que produziu os 55%, os 19,3% e o selo
  VERIFIED. Qualquer número novo precisa de artefato que terceiro reproduza.
- **Comparativo com outros frameworks** sem rodar os outros frameworks. Uma tabela
  comparativa sem execução é opinião formatada como dado.

---

## Ordem sugerida, se houver apetite

1. **A**, com corpus externo — é o único item com caminho curto até algo que
   alguém usaria, e reaproveita o que a Fase 1 construiu.
2. **B**, quando houver orçamento — barato em código, caro em credibilidade se mal
   feito, e é a única forma de reivindicar qualquer coisa sobre tokens.
3. **C**, apenas se houver histórico de incidentes para calibrar.

O item A pode começar hoje, sem credenciais e sem custo de API.
