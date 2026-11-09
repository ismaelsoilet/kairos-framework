# Playbook Operacional KAIROS: Casos de Uso Reais

Este guia fornece orientações passo a passo para aplicar o framework KAIROS em 4 cenários práticos e realistas de engenharia de software.

---

## ⚡ Caso de Uso 1: O Hotfix de UI em 2 Minutos (Modo Alpha)

### O Cenário
Você precisa corrigir o padding de um botão, a cor de hover e adicionar uma tag `aria-label` de acessibilidade em um componente React/Vue (`UserProfileCard.vue`).

### O Anti-Padrão (Desperdício Monolítico)
Sem o KAIROS, um agente gastaria mais de 150.000 tokens criando documentos de arquitetura, abrindo enxames de 5 subagentes e gerando mocks pesados de backend para uma alteração de 4 linhas de CSS.

### O Jeito KAIROS (Modo Alpha)

1. **Classificação pelo Dial:**
   ```bash
   python3 scripts/kairos_cli.py dial "Ajustar padding e adicionar aria-label no botao salvar de UserProfileCard"
   # Saída: [ MODO ALPHA ] - Teto de 15.000 tokens - Zero subagentes
   ```

2. **Declaração de Intenção no Chat (Sem arquivos extras):**
   > *"Operando sob KAIROS Modo Alpha. Alvo: `src/components/UserProfileCard.vue`. Alterações: adicionar classe `p-3`, cor hover `#2563eb` e `aria-label='Salvar Perfil'`. Edição direta sem worktree."*

3. **Edição Cirúrgica Direta:**
   O agente edita diretamente o arquivo do componente.

4. **Diff & Sanity Check de Acessibilidade:**
   Inspeciona o `git diff` para garantir que nenhum CSS global vazou e nenhum código morto foi deixado:
   ```bash
   git diff src/components/UserProfileCard.vue
   ```

* **Custo em tokens deste cenário: não medido.** Versões anteriores desta página
  afirmavam "~6.800 tokens" e "mais de 90% de economia vs monólito". Nenhum dos
  dois foi medido — eram estimativas escritas como observações. Retirados (ver
  `RETRACTION.md`). Esta página descreve *como o processo funciona*, não quanto
  ele custa.

---

## 🚀 Caso de Uso 2: Feature Brownfield com Retrocompatibilidade (Modo Beta)

### O Cenário
Adicionar um novo filtro de `status` e paginação baseada em cursor em um endpoint existente (`GET /api/v1/pedidos`), garantindo que aplicativos legados continuem funcionando sem alterações.

### O Jeito KAIROS (Modo Beta)

1. **Classificação pelo Dial:**
   ```bash
   python3 scripts/kairos_cli.py dial "Adicionar filtro de status e paginacao por cursor na rota de pedidos"
   # Saída: [ MODO BETA ] - Teto de 65.000 tokens - Quota de 1 subagente
   ```

2. **Criação da Delta Spec:**
   ```bash
   python3 scripts/kairos_cli.py spec pedidos_paginacao_cursor
   ```
   Preenche `.kairos/changes/<id>/specs.md`:
   * **Adicionado:** Parâmetros `cursor` (string, opcional) e `status` (enum, opcional).
   * **Invariantes:** Chamadas sem o parâmetro `cursor` utilizam a ordenação padrão anterior, sem quebrar clientes existentes.

3. **Criação de Git Worktree Isolada:**
   ```bash
   python3 scripts/kairos_cli.py worktree create pedidos_paginacao_cursor
   cd .kairos/worktrees/pedidos_paginacao_cursor
   ```

4. **Ciclo TDD Estrito:**
   * **Fase Vermelha (Red):** Escreve `tests/api/pedidos_paginacao.spec.ts`. Roda o teste -> Confirma falha.
   * **Fase Verde (Green):** Implementa a query no repositório `src/pedidos/service.ts`. Roda o teste -> Passa.
   * **Fase de Refatoração:** Limpa a consulta SQL.

5. **Auditoria Adversarial no Diff:**
   ```bash
   python3 scripts/kairos_cli.py audit --base main
   # Saída: [ ✅ VERIFIED ] - Zero fraudes, testes intactos.
   ```

6. **Promover Documentação Viva e Limpeza:**
   ```bash
   python3 scripts/kairos_cli.py archive pedidos_paginacao_cursor
   python3 scripts/kairos_cli.py worktree remove pedidos_paginacao_cursor
   ```

---

## 🔒 Caso de Uso 3: Transação Financeira Crítica (Modo Gamma)

### O Cenário
Construir um serviço atômico de transferência de saldo bancário onde múltiplas requisições simultâneas podem gerar condições de corrida (*race conditions*) e saldo duplicado.

### O Jeito KAIROS (Modo Gamma)

1. **Classificação pelo Dial:**
   ```bash
   python3 scripts/kairos_cli.py dial "Refatorar transferencia de saldo com travas de concorrencia e auditoria"
   # Saída: [ MODO GAMMA ] - Teto de 180.000 tokens - Suite Completa Zero-Trust
   ```

2. **Revisão Fria pelo Crítico Goldfish (`kairos_critic`):**
   A Delta Spec é analisada pelo subagente `kairos_critic` (sem memória da conversa anterior). O crítico alerta:
   > *"[CRITICAL-01] A especificação menciona checar o saldo, mas não exige lock a nível de linha ou mutex. Sob alta concorrência de threads, ocorrerá gasto duplo."*

3. **Implementação com TDD e Mutex:**
   O desenvolvedor implementa a trava via `threading.Lock()` ou `SELECT FOR UPDATE` no banco.

4. **Verificação de Força dos Testes com K-Mutant:**
   ```bash
   python3 scripts/kairos_cli.py mutate src/wallet/account.py --test "pytest tests/test_account.py" --max-mutants 10
   # Saída: MUTATION SCORE: 100.0% (Killed: 10 | Survived: 0)
   ```
   *Comprovação matemática de que os testes realmente quebram se alguém inverter os sinais matemáticos ou operadores booleanos!*

5. **Auditoria Adversarial e Portão Final:**
   ```bash
   python3 scripts/kairos_cli.py audit --base main
   python3 scripts/kairos_cli.py status --dashboard
   ```
   Veredito: **READY**. Spec arquivada em `.kairos/specs/wallet_atomic_transfers.md`.

---

## 🤖 Caso de Uso 4: Automação em Pipelines de CI/CD (GitHub Actions Gatekeeper)

A CLI do KAIROS pode rodar dentro do GitHub Actions ou GitLab CI para barrar automaticamente Pull Requests que contenham fraudes de IA, testes comentados ou baixa cobertura de mutação.

### `.github/workflows/kairos-gate.yml`
```yaml
name: KAIROS Zero-Trust Quality Gate

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Executar Auditoria de Diff Anti-Fraude
        run: |
          python3 scripts/kairos_cli.py audit --base origin/main

      - name: Executar Teste de Mutação nos Arquivos Alterados
        run: |
          python3 scripts/kairos_cli.py mutate src/core/service.py --test "npm test" --max-mutants 10
```

* **Resultado:** Qualquer PR em que um agente de IA tenha desativado testes (`.skip()`), apagado asserções ou deixado blocos vazios de `except/catch` será **reprovado automaticamente na esteira de integração contínua** antes de chegar aos revisores humanos.
