# 🛡️ PROTOCOLO DE AUDITORIA ADVERSARIAL INDEPENDENTE (ZERO-TRUST) - V3 (CALIBRADO)
## Benchmark Empírico: KAIROS Framework vs. Vibe Coding (Vanilla)

Este documento foi projetado para ser fornecido diretamente a **qualquer agente autônomo, LLM ou harness independente** (ex.: **Command Code / Claude Code**, **Cursor**, **Windsurf**, **Codex**, **OpenHands**, **DeepSeek**, **Gemini CLI**).

O agente auditor deve operar sob **Confiança Zero (Zero-Trust)**:
> *"Nenhuma alegação de texto, arquivo JSON estático ou narrativa prévia deve ser aceita como verdade. Toda alegação deve ser testada e comprovada fisicamente no terminal e na rede local."*

---

## 📋 PROMPT CALIBRADO PARA COPIAR E COLAR NO SEU AGENTE / HARNESS EXTERNO

```markdown
Você é um Auditor Adversarial de Engenharia de Software e Qualidade (Principal Zero-Trust QA Auditor).
Você recebeu a missão de auditar de forma independente um benchmark comparativo entre dois projetos desenvolvidos sob a mesma especificação:
1. "Vanilla Project" (Porta 5051): Código gerado via Vibe Coding tradicional.
2. "KAIROS Project" (Porta 5052): Código gerado sob o framework de governança KAIROS (Modo GAMMA: Delta Spec, TDD estrito, AsyncMutex, K-Mutant e Auditoria de Diff).

DIRETIVA SUPREMA DE AUDITORIA:
- NÃO confie em nada que esteja escrito nos relatórios ou na documentação.
- Assuma que todas as alegações podem ser fabricadas ou simuladas até que você execute pessoalmente os comandos e inspecione os bytes e os códigos de saída (exit codes) no terminal.
- Se algum comando falhar ou a saída divergir dos critérios estabelecidos, emita o veredito [ ❌ REFUTED ].
- Se todas as 6 alegações empíricas forem reproduzidas fisicamente, emita o veredito [ ✅ VERIFIED ].

Execute no terminal cada uma das 6 etapas a seguir:

================================================================================
ETAPA 1: VERIFICAÇÃO DE SAÚDE E TELEMETRIA DINÂMICA DE TOKENS (ZERO HARDCODING)
================================================================================
Comandos:
  export PATH="$HOME/.nvm/versions/node/v24.13.0/bin:$PATH"
  curl -s http://localhost:5051/api/health
  curl -s http://localhost:5052/api/health
  curl -s http://localhost:5052/api/metrics | grep -o '"liveCodebaseTokens":[^,]*'

Critérios de Aceite:
1. Vanilla (5051): Deve responder status 'ok' e registrar ausência de governança (Vibe Coding).
2. KAIROS (5052): Deve responder status 'healthy', com governança 'Zero-Trust Verified', lendo dinamicamente de .kairos/audit_latest.json e .kairos/kmutant_latest.json com timestamps válidos e correspondentes ao mtime dos arquivos.
3. A métrica 'liveCodebaseTokens' deve ser calculada em tempo real via tokenizer BPE (gpt-tokenizer) sobre os arquivos físicos do código.
   [Teste de Fraude]: Abra kairos-project/src/calculator.js, adicione um comentário de 5 palavras, chame o endpoint /api/metrics novamente e certifique-se de que o número de tokens aumentou proporcionalmente. Em seguida, desfaça a alteração.

================================================================================
ETAPA 2: PROVA DE CONCORRÊNCIA E RACE CONDITION EM ALTA CARGA
================================================================================
Comandos:
  python3 /home/ismaelsoilet/kairos-vs-vanilla-benchmark/benchmark_suite.py

  # Teste isolado dos códigos de status HTTP do KAIROS:
  python3 -c '
  import urllib.request, urllib.error, json
  from concurrent.futures import ThreadPoolExecutor
  from collections import Counter
  urllib.request.urlopen(urllib.request.Request("http://localhost:5052/api/reset-vip", data=b"{}", headers={"Content-Type": "application/json"}))
  def req(i):
      try:
          r = urllib.request.urlopen(urllib.request.Request("http://localhost:5052/api/reserve-vip", data=json.dumps({"seats": 1, "requester": f"u-{i}"}).encode(), headers={"Content-Type": "application/json"}))
          return r.status
      except urllib.error.HTTPError as e:
          return e.code
  with ThreadPoolExecutor(max_workers=50) as p:
      codes = list(p.map(req, range(50)))
  print("Status Codes KAIROS:", Counter(codes))
  '

Critérios de Aceite:
1. Sob 50 requisições simultâneas de reserva VIP:
   - Vanilla (5051): Deve apresentar RACE CONDITION e sobre-reserva crítica (50 sucessos para uma capacidade limite de 10 assentos, corrompendo o saldo).
   - KAIROS (5052): Deve alocar com precisão atômica via AsyncMutex exatamente 10 reservas (HTTP 200) e rejeitar exatamente 40 (HTTP 409 Conflict), deixando exatamente 0 assentos restantes.
2. Desempenho de Carga: Throughput (RPS) e Latência média do KAIROS devem ser estatisticamente equivalentes aos do Vanilla (diferença inferior a 5%), comprovando que a blindagem atômica por AsyncMutex não impõe gargalo perceptível.

================================================================================
ETAPA 3: AUDITORIA ADVERSARIAL NO HISTÓRICO DO GIT (HUNTING DAS 6 FRAUDES)
================================================================================
Comandos:
  cd /home/ismaelsoilet/kairos-vs-vanilla-benchmark/vanilla-project
  python3 /home/ismaelsoilet/kairos-framework/scripts/kairos_cli.py audit --base main
  echo "Vanilla Exit Code: $?"

  cd /home/ismaelsoilet/kairos-vs-vanilla-benchmark/kairos-project
  python3 /home/ismaelsoilet/kairos-framework/scripts/kairos_cli.py audit --base main
  echo "KAIROS Exit Code: $?"

Critérios de Aceite:
1. Vanilla: O auditor algorítmico do KAIROS deve retornar [ ❌ REFUTED ] com Exit Code 1, apontando 5 detecções de violações:
   - Asserção de teste comentada em tests/test_calculator.js (`// assert.strictEqual(...)`).
   - 4 detecções de blocos de exceção vazios / falhas silenciosas (`catch (err) {}` e `} catch (_) {}`).
2. KAIROS: O auditor deve retornar [ ✅ VERIFIED ] com Exit Code 0 (zero violações, zero testes desativados, zero stubs fantasmas em todo o repositório).

================================================================================
ETAPA 4: TESTE DE MUTAÇÃO K-MUTANT (RIGOR REAL DOS TESTES UNITÁRIOS)
================================================================================
Comandos:
  cd /home/ismaelsoilet/kairos-vs-vanilla-benchmark/vanilla-project
  python3 /home/ismaelsoilet/kairos-framework/scripts/kairos_cli.py mutate src/calculator.js --test "npm test"

  cd /home/ismaelsoilet/kairos-vs-vanilla-benchmark/kairos-project
  python3 /home/ismaelsoilet/kairos-framework/scripts/kairos_cli.py mutate src/calculator.js --test "npm test"

Critérios de Aceite:
1. Baseline: Ambos os repositórios passam em `npm test` isolado com Exit Code 0.
2. Vanilla: Kill Rate de apenas ~30.0% (7 de 10 mutantes sintéticos sobrevivem sem que a suíte `npm test` perceba, comprovando a ilusão de 100% de cobertura verde).
3. KAIROS: Kill Rate de 100.0% (10 de 10 mutantes mortos pela suíte do KAIROS, comprovando que cada operador lógico e branch é estritamente asserido).

================================================================================
ETAPA 5: AUDITORIA REAL DE TOKENS E EXECUÇÃO FÍSICA DO GOOGLE GEMINI 3.8 FLASH
================================================================================
Comando:
  python3 /home/ismaelsoilet/kairos-vs-vanilla-benchmark/real_gemini_benchmark/run_real_gemini_benchmark.py

Critérios de Aceite:
O script inspeciona os arquivos JSONL físicos de telemetria da infraestrutura do Google Gemini (`transcript.jsonl`) e executa em runtime o código gerado em cada fase:
1. Divisão Real de Fases (Subagente 1 - Vibe Coding):
   - Turno 1 (Steps 0–26: geração inicial + testes ingênuos + setup): 61.557 tokens ativos (56.167 in + 5.390 out; 326.206 cache).
   - Turno 2 (Steps 27–38: ciclo real de reparo pós-notificação de bug de concorrência): 50.762 tokens ativos (46.730 in + 4.032 out; 174.556 cache).
   - Total Consolidado Vibe: 112.319 tokens ativos (102.897 in + 9.422 out) e 500.762 cache read.
2. Abordagem KAIROS (Subagente 2 - Governança Modo GAMMA):
   - Turno Único: 16 Respostas LLM com Tokens (steps 0–32 do transcript: Delta Spec + TDD estrito + AsyncMutex): 90.676 tokens ativos (69.589 in + 21.087 out, incluindo 9 retentativas operacionais de tool calls) e 319.139 cache read.
   - Retrabalho de Código: 0 tokens (zero reparo necessário; aprovado na 1ª passagem).
3. Balanço de Economia Líquida:
   - Economia Ativa (In+Out): 21.643 tokens poupados pelo KAIROS (19.3%).
   - Economia com Cache Read: 203.266 tokens poupados pelo KAIROS (33.15%).
4. Execução Física em Runtime (evaluate_live_gemini.js):
   - Código Vibe Inicial (Step 9): Sob 60 threads, autoriza 60/50 e termina com saldo -R$ 100 (❌ Falha Crítica comprovada fisicamente).
   - Código Vibe Reparado (Step 28): Sob 60 threads, autoriza 50 e rejeita 10 com saldo R$ 0 (✅ Seguro após retrabalho).
   - Código KAIROS: Sob 60 threads, autoriza 50 e rejeita 10 com saldo R$ 0 (✅ 100% Atômico na 1ª passagem).
5. Esclarecimento Metodológico: O auditor deve observar que a tese do KAIROS é a especificação prévia (Delta Spec). O prompt do KAIROS exigiu AsyncMutex porque o framework força a identificação de concorrência antes da escrita do código, enquanto o Vibe Coding gerou código a partir de requisitos informais e descobriu a concorrência na quebra de produção.

================================================================================
ETAPA 6: HEADERS DE SEGURANÇA E CONFORMIDADE WEB
================================================================================
Comandos:
  curl -sI http://localhost:5051/ | grep -iE 'content-security-policy|x-content-type-options|x-frame-options'
  curl -sI http://localhost:5052/ | grep -iE 'content-security-policy|x-content-type-options|x-frame-options'

Critérios de Aceite:
1. Vanilla (5051): Retorna 0/4 headers de proteção (vulnerável a clickjacking, MIME sniffing e XSS).
2. KAIROS (5052): Retorna 4/4 headers obrigatórios (Content-Security-Policy estrito, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy).

================================================================================
FORMATO OBRIGATÓRIO DE RESPOSTA DO AUDITOR
================================================================================
Após executar todos os comandos acima, emita o seu relatório contendo:
1. Tabela Formal de Evidências com as 6 etapas:
   - Requisito
   - Comando Executado
   - Saída Observada
   - Status (CONFIRMADO / REFUTADO)
2. Análise da armadilha do Vibe Coding (por que o custo de reparo superou o custo da engenharia orientada a especificação).
3. Veredito Final: [ ✅ VERIFIED ] ou [ ❌ REFUTED ].
```
