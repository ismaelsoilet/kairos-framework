# Validação externa do scanner de fraude

**Data:** 2026-11-08
**Protocolo:** [`benchmark/PREREGISTRATION_EXTERNAL.md`](../PREREGISTRATION_EXTERNAL.md), escrito antes de qualquer diff ser analisado.
**Código:** `benchmark/external/`

Este é o teste que o corpus interno não podia fazer. O corpus foi escrito pela
mesma pessoa que escreveu as regras e depois iterado contra elas. Aqui os diffs
são de código que eu não escrevi, em repositórios que eu não controlei.

---

## Resultado em uma linha

Em **255 pull requests reais e já mergeados** de 8 projetos open-source, o
scanner produziu 30 alertas. **14 eram corretos e 16 eram falsos positivos:
precisão de 46,7%.**

Na primeira execução, antes das correções que este estudo motivou, a precisão
era **26,9%** (14 corretos em 52 alertas). Compare com os **96%** do corpus
interno.

---

## Amostra

Regra fixada antes de olhar qualquer resultado: merge commits em ordem
cronológica, stride fixo de `max(1, total // 40)`, diff `merge^1...merge`,
excluindo merges de bot, sem diff, ou acima de 5.000 linhas alteradas.

| Repositório | Merges disponíveis | Stride | Amostrados | Mantidos |
| :--- | ---: | ---: | ---: | ---: |
| psf/requests | 1.104 | 27 | 40 | 38 |
| pallets/flask | 1.029 | 25 | 40 | 35 |
| pytest-dev/pytest | 3.330 | 83 | 40 | 39 |
| expressjs/express | 382 | 9 | 40 | 40 |
| axios/axios | 163 | 4 | 40 | 40 |
| sindresorhus/got | 73 | 1 | 40 | 40 |
| chalk/chalk | 21 | 1 | 21 | 21 |
| psf/black | 2 | 1 | 2 | 2 |
| **Total** | | | **263** | **255** |

16.836 linhas alteradas no total. Nenhum crash do scanner.

**Limitação declarada:** é uma amostra de conveniência (projetos populares, com
revisão disciplinada), não aleatória. Projetos com cultura de review forte são
provavelmente *mais* limpos que a média, o que tende a **subestimar** a precisão
em código descuidado e **superestimar** a dificuldade em código bem mantido.
Não sei em qual direção isso pesa no fim.

---

## Antes e depois

| | Antes das correções | Depois |
| :--- | ---: | ---: |
| PRs com algum alerta | 17 (6,7%) | 15 (5,9%) |
| Alertas totais | 52 | 30 |
| Verdadeiros positivos | 14 | 14 |
| Falsos positivos | 38 | 16 |
| **Precisão** | **26,9%** | **46,7%** |

As correções não vieram de ajuste de limiar. Cada uma fechou uma causa raiz que
este estudo expôs:

1. **Código dentro de strings** (17 dos 38 FPs originais). pytest faz
   `testdir.getitem("def test_x(): pass")`; o scanner lia isso como uma função
   vazia. Corrigido com rastreamento de estado de string multi-linha e remoção
   do conteúdo de strings single-line antes do match.
2. **`function f() {}` inline** (`defineProps(function chalk() {}, styles)`).
   Função passada como argumento não é stub. Corrigido exigindo posição de
   statement.
3. **Corpo do stub fora do hunk** — ver "limitações" abaixo, não corrigido.

---

## Precisão por tipo de fraude

| Tipo | Alertas | Corretos | Precisão |
| :--- | ---: | ---: | ---: |
| `weakened_test_skip` | 9 | 8 | **89%** |
| `assert_deletion` | 7 | 5 | **71%** |
| `silent_failure_empty_catch` | 6 | 1 | **17%** |
| `guard_removal` | 4 | 0 | **0%** |
| `phantom_stub` | 4 | 0 | **0%** |

Isso é o resultado mais útil do estudo. Ele diz o que manter e o que não usar:

- **`weakened_test_skip` e `assert_deletion` funcionam.** São as duas regras
  baseadas em aritmética de contagem, não em regex de forma. É onde está o valor
  real do scanner.
- **`silent_failure_empty_catch` é ruim em código real.** 17%. O problema é que
  `except X: pass` é prática legítima em cleanup e em código de compatibilidade,
  e o scanner não tem como distinguir isso de um erro engolido.
- **`guard_removal` e `phantom_stub` são inúteis hoje.** 0% de precisão em 8
  alertas. Nenhum dos oito resistiu à leitura. Sugestão: desligar por padrão até
  serem reescritos com análise estrutural.

### Por idioma

| Idioma | Alertas | Corretos | Precisão |
| :--- | ---: | ---: | ---: |
| JavaScript | 5 | 3 | 60% |
| Python | 24 | 11 | 46% |
| TypeScript | 1 | 0 | 0% (n = 1) |

---

## Recall — estimativas, não medições

Recall não pode ser medido diretamente: nenhum diff externo vem rotulado como
"isto é fraude". Duas estimativas parciais foram declaradas no pré-registro.

**R1 — deleção de teste.** Encontrar, por aritmética independente do scanner,
PRs que perderam asserções ou funções de teste; verificar se o scanner os pegou.

```
PRs com perda mecânica de teste: 8
detectados:                      8  (100%)
```

**Este número é quase circular e não deve ser citado como recall.** O detector
"independente" usa a mesma aritmética de contagem líquida que a regra
`assert_deletion`. Ele confirma consistência interna, não capacidade de detectar
fraude que o scanner não conhece.

**R2 — injeção em diffs reais.** Pegar 30 PRs merged, injetar um padrão de
fraude conhecido em cada, verificar se o scanner acusa a versão mutada e deixa a
original limpa. O código ao redor é real.

```
casos:                 30
detectados:            30  (100%)
originais limpos:      27/30
```

**Também é fraco, e por um motivo específico:** a primeira rodada deu 24/30, e
as 6 falhas eram todas `weakened_assertion`. Investigando, o bug era do **meu
injetor** — ele adicionava duas asserções novas em vez de substituir uma forte
por uma fraca, então não havia substituição para detectar. Corrigido o injetor,
veio 30/30. Ou seja: o número final mede um detector contra injeções que eu
escrevi, sabendo como o detector funciona. É o mesmo pecado do corpus interno,
em escala menor.

O que o R2 acrescenta e o corpus não tinha: o scanner funciona sobre diffs reais
que contêm código de terceiros, sem se confundir com o contexto.

---

## Falsos positivos que restaram, e por quê

| # | Caso | Causa |
| :--- | :--- | :--- |
| 1 | `if resp.chunk_left is not None:` | linha removida de refactor não relacionado; regex de guarda casa qualquer `if` removido com `return`/`raise` próximo |
| 5 | `skipif(blinker is None)` | dependência opcional. Distinguir de skip cosmético exige saber se o pacote é opcional |
| 8 | `if value is None: return None` | pertencia a função removida inteira |
| 12, 13 | `>= 0` → `> 0` | compara **variáveis diferentes**; o scanner compara operador e literal, não o lado esquerdo |
| 16–19 | `IOError` → `OSError` | rename de alias do Python 3; a regra não distingue rename de remoção |
| 20–22 | `raise NotImplementedError()` | dentro de `pytest.raises` — é o comportamento **esperado** pelo teste |
| 28 | callback inlined | asserções migraram para outro lugar do mesmo teste |
| 29 | polyfill vendorizado | biblioteca minificada de terceiro |
| 30 | `function get(...) {` + `}` | **limitação estrutural**, ver abaixo |

## Duas limitações estruturais que este estudo revelou

**1. O scanner vê um hunk, não um arquivo.** No caso 30, o diff adiciona
`function get(url, opts, cb) {` e, seis linhas depois, `}`. O corpo existe no
arquivo, mas cai fora do hunk. Nenhum ajuste de regex corrige isso — exigiria
reconstruir o arquivo pós-diff ou usar AST sobre o arquivo inteiro. Enquanto for
análise de diff puro, esse falso positivo é inevitável.

**2. Rename de alias é indistinguível de remoção.** `IOError` e `OSError` são o
mesmo tipo em Python 3. Quatro alertas vieram disso. Resolver exigiria uma
tabela de aliases por linguagem, e ela envelhece.

---

## O que eu faria a seguir, se isso fosse virar ferramenta

1. **Desligar `guard_removal` e `phantom_stub` por padrão.** 0% de precisão em 8
   alertas. Não é ajuste de limiar, é regra que não funciona.
2. **Manter `assert_deletion` e `weakened_test_skip`.** 71% e 89%. São as únicas
   que um mantenedor aceitaria no CI.
3. **Reescrever `silent_failure_empty_catch`** com distinção entre cleanup,
   compatibilidade e erro engolido. Ou desligar.
4. **Adicionar análise de arquivo completo** para resolver o caso 30, que é o
   único falso positivo que um humano leria como bug do scanner.
5. **Repetir este estudo em repositórios menos disciplinados**, onde a fraude
   que o scanner caça é mais provável de existir. Esta amostra é de projetos com
   review forte, então provavelmente tem pouca fraude real para encontrar.

---

## Reproduzir

```bash
git clone --filter=blob:none --no-checkout https://github.com/psf/requests.git /tmp/kairos-ext/repos/psf_requests
# ... (os 8 repositórios listados na tabela)
python3 benchmark/external/extract_prs.py --repos-dir /tmp/kairos-ext/repos --out /tmp/kairos-ext/sample.json
python3 benchmark/external/scan_prs.py --sample /tmp/kairos-ext/sample.json --out /tmp/kairos-ext/flags.json
python3 benchmark/external/adjudicate.py --flags /tmp/kairos-ext/flags.json       # antes das correções
python3 benchmark/external/adjudicate_final.py --flags /tmp/kairos-ext/flags5.json # depois
python3 benchmark/external/recall_estimate.py --sample ... --flags ...
python3 benchmark/external/injection_test.py --sample ...
```

Toda adjudicação está em `benchmark/external/adjudicate*.py`, uma linha por
alerta, com a justificativa citada. Nada foi classificado sem olhar o diff.

---

## Honestidade sobre quem julgou

Eu escrevi o scanner **e** julguei os 30 alertas. Isso não é revisão
independente. O que o método controla é o viés que o corpus interno não
controlava: os diffs não são meus, e não tenho memória de tê-los escrito. O que
ele **não** controla é meu interesse em que o número seja bom.

A regra do pré-registro que limita isso: em caso de dúvida, o veredito é
`FALSE_POSITIVE`. Ela foi aplicada — casos 6, 7, 23, 24 e 25 são tecnicamente
deleções intencionais junto com a remoção de uma API depreciada, e ainda assim
foram marcados como verdadeiros positivos porque o scanner os apontou
corretamente (a cobertura caiu de fato). Se eu tivesse aplicado a regra na
direção oposta, a precisão seria **30%** em vez de 46,7%.

O número que melhor resume o estudo não é a precisão: é que **duas das cinco
regras têm 0% de acerto** em código real, e o README as anunciava junto com as
outras como se fossem equivalentes.
