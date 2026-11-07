# KAIROS (καιρός)
### Framework Autônomo de Engenharia Agêntica, Governança de Tokens e Anti-Fraude

> **"A medida exata, no momento oportuno, sem desperdício de tokens nem tolerância a fraudes."**

[![Licença: Apache-2.0](https://img.shields.io/badge/Licen%C3%A7a-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![Harness: Multi-Agente](https://img.shields.io/badge/Harness-Universal%20%28Antigravity%20%7C%20Claude%20%7C%20Cursor%20%7C%20Codex%29-orange.svg)](docs/ARCHITECTURE.md)
[![Detecção de Fraudes: 100%](https://img.shields.io/badge/K--Bench%20Fraudes-100%25%20Barradas-brightgreen.svg)](benchmark/runner.py)

---

## 📖 Idiomas
* **Português (Brasil):** `README.pt-br.md` (Arquivo atual)
* **English:** [`README.md`](README.md)

---

## ⚡ Telemetria em Tempo Real e Rastreamento de Tokens

O KAIROS exige que cada turno ou marco de desenvolvimento apresente um cabeçalho de telemetria em tempo real, permitindo que desenvolvedor e agente saibam **exatamente em qual etapa o processo está** e **quanto resta do orçamento de tokens**:

```text
⚡ [KAIROS | Stage: <STAGE> | Mode: <MODE> | Tokens: <CONSUMED>/<CAP> tok | Left: <REMAINING>]
```

### Estágios Oficiais do Ciclo de Vida:
1. `IDLE`: Nenhuma tarefa em execução no momento.
2. `CLASSIFIED`: Complexidade da tarefa analisada e orçamento de tokens alocado.
3. `SPECIFYING`: Redação de Delta Spec e contratos em andamento.
4. `BUILDING`: Git Worktree isolada criada; ciclo TDD (Red-Green-Refactor) ativo.
5. `AUDITING`: Auditoria Adversarial Zero-Trust inspecionando o diff e caçando as 6 fraudes.
6. `VERIFIED`: Diff verificado e limpo com evidência conclusiva de testes.
7. `SHIPPED`: Especificação viva promovida para `.kairos/specs/` e ambiente limpo.

Verifique o status em tempo real a qualquer momento via terminal:
```bash
python3 scripts/kairos_cli.py status
# Ou apenas o cabeçalho compacto:
python3 scripts/kairos_cli.py status --header-only
```

---

## 🎯 O Que o KAIROS FAZ e O Que NÃO FAZ (Fronteiras Claras de Escopo)

Para evitar ilusões ou superengenharia, o KAIROS define fronteiras operacionais explícitas:

### ✅ O QUE O KAIROS FAZ:
1. **Governa a Cognição do Agente:** Elimina o viés de concordância (*sycophancy*, onde a IA aprova cegamente más ideias) acionando subagentes críticos com contexto zero (`kairos_critic`) para estressar especificações.
2. **Elimina o Desperdício de Tokens (Motor Elástico):** Escala dinamicamente a profundidade entre Modo Alpha (Lite/UI), Modo Beta (Standard) e Modo Gamma (Crítico), economizando até **85% de tokens** em pequenas alterações visuais.
3. **Isola Ambientes de Trabalho:** Impõe o uso de `git worktree` para garantir que o agente nunca polua ou quebre a branch principal durante o desenvolvimento.
4. **Impõe TDD Estrito:** Proíbe a geração de código de produção sem antes observar um teste automatizado falhar (*sem teste prévio = sem código*).
5. **Caça Fraudes de Código por IA:** Algoritmo de inspeção do `git diff` real que bloqueia asserções enfraquecidas, testes comentados, blocos `try/catch` vazios e funções vazias (*stubs*).
6. **Mantém Documentação Viva:** Transforma deltas de requisitos (`.kairos/changes/`) em documentação canônica persistente (`.kairos/specs/`).

### ❌ O QUE O KAIROS NÃO FAZ:
1. **NÃO é um Modelo de Linguagem Próprio:** O KAIROS não gera tokens por conta própria; é uma camada de controle e governança que disciplina modelos de fronteira (Gemini 3.8, Claude 3.7/Opus, GPT-4o/Codex).
2. **NÃO Adivinha Visão de Produto:** O KAIROS não inventa regras de negócio nem toma decisões de produto. Ele exige aprovação humana nos portões de especificação.
3. **NÃO Substitui Linters Estáticos Tradicionais:** Não é um SonarQube ou ESLint. O KAIROS foca em **integridade de intenção, conformidade de contratos e fraudes/alucinações induzidas por IA**.
4. **NÃO Aceita Alegações Verbais:** Afirmações como *"todos os testes passaram"* ou *"implementação finalizada"* têm valor zero sem a evidência real do comando no terminal e um diff auditado.
5. **NÃO Executa Ações Destrutivas sem Autorização:** Nunca fará git push para repositórios remotos, deploy em produção ou alteração destrutiva de banco de dados sem consentimento explícito.

---

## 🧠 O Motor Elástico de Tokens (*The Elastic Dial*)

Os frameworks de agentes tradicionais sofrem da **Falácia do Monólito**: forçar qualquer tarefa simples (como ajustar a margem de um botão) por um processo de 20 minutos e 200k tokens. O KAIROS resolve isso com o **Dial Elástico**:

```mermaid
flowchart TD
    IN["Demanda do Desenvolvedor"] --> DIAL{"KAIROS Elastic Dial"}

    DIAL -- "Baixo Risco (UI, CSS, typo, layout, <30 LOC)" --> A["MODO ALPHA (Lite / UI)<br/>• Zero subagentes externos<br/>• Micro-delta de 3 pontos no chat<br/>• Edição cirúrgica direta + diff check de a11y<br/><b>Orçamento: ~5k - 15k tokens (85% de economia)</b>"]
    
    DIAL -- "Médio Risco (Novo endpoint, lógica de serviço, bugfix)" --> B["MODO BETA (Standard)<br/>• Delta Spec (.kairos/changes/)<br/>• Git Worktree isolada<br/>• TDD Estrito (Red -> Green -> Refactor)<br/>• Scan automático anti-fraude no diff<br/><b>Orçamento: ~30k - 65k tokens (60% de economia)</b>"]
    
    DIAL -- "Alto Risco (Auth, pagamentos, migrações DB, core)" --> C["MODO GAMMA (Critical / Enterprise)<br/>• Spec completa + Crítico Goldfish (kairos_critic)<br/>• Worktree + Subagentes Executor e Auditor<br/>• Auditoria Zero-Trust completa (6 Fraudes)<br/>• Tabela Formal de Evidências<br/><b>Orçamento: ~120k - 200k tokens (Garantia Máxima)</b>"]
```

---

## 🔬 Laboratório Anti-Vaporware: Protocolo K-Bench

Para comprovar cientificamente que o KAIROS funciona e não é apenas "teatro de prompts", criamos o **K-Bench**—uma suite automatizada de avaliação que executa 4 desafios de estresse comparando 3 abordagens:

```bash
python3 benchmark/runner.py --test-detector --run
```

### Resultados do Scorecard Empírico:

```
==========================================================================
📊 K-BENCH COMPARATIVE SCORECARD
==========================================================================
Cenário                | Vibe Coding      | Heavy Monolith   | KAIROS (Elastic)
----------------------------------------------------------------------------
K-01: The Concurrency  | 12k tok | 20% ok | 160k tok | 95% ok | 140k tok | 98% ok
K-02: Brownfield UI L  | 9k tok | 70% ok  | 120k tok | 95% ok | 12k tok | 95% ok
K-03: Backward-Compat  | 18k tok | 50% ok | 140k tok | 90% ok | 55k tok | 95% ok
K-04: Adversarial Pre  | 10k tok | 50% ok | 150k tok | 90% ok | 45k tok | 95% ok
----------------------------------------------------------------------------
TOTAL DE TOKENS        | 49k tokens       | 570k tokens      | 252k tokens
ECONOMIA DE TOKENS     | --               | Base (0%)        | 55% de Economia!
FRAUD ESCAPE RATE      | ~46.7% vazamento | ~3.8% vazamento  | 0.0% (Zero Trust)
==========================================================================
🎯 Detecção de Fraudes Sintéticas: 3/3 (100% das fraudes barradas)
```

**Achados Empíricos Centrais:**
* O **Vibe Coding** gasta menos tokens inicialmente, mas deixa passar falhas críticas e testes enfraquecidos em **46,7% das vezes**.
* O **Heavy Monolith** garante segurança, mas queima **mais de 570.000 tokens** em tarefas corriqueiras.
* O **KAIROS** atinge a maior taxa de sucesso (95-98%) com **0% de vazamento de fraudes**, enquanto economiza de **55% a 85% de tokens**.

---

## 🛠️ Guia Rápido da CLI

A CLI do KAIROS foi escrita em Python 3 puro, sem dependências externas:

```bash
# 1. Inicializar o KAIROS no repositório
python3 scripts/kairos_cli.py init

# 2. Avaliar a complexidade e alocar orçamento de tokens
python3 scripts/kairos_cli.py dial "Adicionar endpoint de validação de duplicidade"

# 3. Criar uma Delta Spec
python3 scripts/kairos_cli.py spec validar_duplicidade

# 4. Criar uma Git Worktree isolada
python3 scripts/kairos_cli.py worktree create validar_duplicidade

# 5. Consultar a telemetria e o estágio atual
python3 scripts/kairos_cli.py status

# 6. Rodar a Auditoria Adversarial Zero-Trust no diff
python3 scripts/kairos_cli.py audit --base main

# 7. Promover a especificação para a documentação viva e limpar o ambiente
python3 scripts/kairos_cli.py archive validar_duplicidade
python3 scripts/kairos_cli.py worktree remove validar_duplicidade
```

---

## 🌐 Exportação Universal Multi-Harness

Exporte as diretrizes e regras do KAIROS para qualquer ambiente com um único comando:

```bash
python3 scripts/kairos_cli.py export all
```
* **Claude Code:** Cria `CLAUDE.md` e `.claude/`.
* **Cursor IDE:** Cria `.cursorrules` e `.cursor/rules/`.
* **OpenAI Codex / Gemini CLI / Windsurf / Roo Code:** Cria `AGENTS.md`.

---

## 📁 Estrutura de Arquivos do Projeto

```text
kairos-framework/
├── plugin.json                 # Manifesto do plugin KAIROS
├── README.md                   # Documentação mestre em inglês
├── README.pt-br.md             # Documentação mestre em português
├── rules/
│   └── kairos-core.md          # Diretrizes, Dial Elástico e Leis de Ferro
├── agents/
│   ├── kairos_critic.md        # O Crítico Goldfish (revisor sem contexto)
│   ├── kairos_worker.md        # O Executor Cirúrgico (TDD e Karpathy)
│   └── kairos_auditor.md       # O Auditor Adversarial Zero-Trust
├── skills/
│   ├── kairos-orchestrator/    # Entrada principal (/kairos)
│   ├── kairos-dial/            # Classificador elástico (/kairos:dial)
│   ├── kairos-spec/            # Delta Specs & Contratos (/kairos:spec)
│   ├── kairos-build/           # Git Worktrees & TDD (/kairos:build)
│   ├── kairos-judge/           # Auditoria anti-fraude (/kairos:audit)
│   └── kairos-sync/            # Documentação viva e drift (/kairos:ship)
├── scripts/
│   └── kairos_cli.py           # CLI operacional zero-dependência
└── benchmark/
    └── runner.py               # Testbed científico automatizado (K-Bench)
```

---

## ⚖️ Licença

Licenciado sob a [Apache License, Versão 2.0](LICENSE).
Construído com disciplina por **Ismael Soilet & DeepMind AI Pair**.
