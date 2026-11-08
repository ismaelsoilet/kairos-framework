# 🔭 KAIROS Scout: O Fim do Problema do Knowledge Cutoff em IAs de Codificação

> **Diagnóstico Honesto, Doutrina Anti-Alucinação e a 4ª Persona Canônica do KAIROS**  
> Como o KAIROS impede que modelos de linguagem usem métodos legados, inventem APIs inexistentes ou ignorem as versões modernas instaladas no projeto.

---

## 1. Diagnóstico Honesto: Isso é Realmente um Problema?

**SIM, É UM DOS PROBLEMAS MAIS DEVASTADORES DO DESENVOLVIMENTO COM IA.**

Todo modelo de linguagem possui uma **data de corte de conhecimento (Knowledge Cutoff)** e um viés estatístico de treinamento dominado por bibliotecas legadas (que possuem milhares de tutoriais antigos na internet).

Quando um desenvolvedor pede para a IA gerar código em um projeto moderno (2025/2026), o agente frequentemente comete os seguintes erros clássicos:

| Biblioteca / Framework | O que a IA tenta fazer (Viés Antigo / Cutoff) | A Realidade Moderna do Projeto | Consequência |
| :--- | :--- | :--- | :--- |
| **Pydantic** | Usa `user.dict()` e `@validator` | Pydantic v2 usa `user.model_dump()` e `@field_validator` | `DeprecationWarning` ou erro em tempo de execução |
| **Next.js** | Cria rotas em `pages/api/` e usa `router.push()` | Next.js 14/15 usa App Router `app/api/` e headers assíncronos | Código totalmente incompatível com a arquitetura |
| **React** | Usa `React.forwardRef` e `defaultProps` | React 19 removeu `forwardRef` (refs agora são props diretas) | `TypeError: forwardRef is not a function` |
| **Tailwind CSS** | Tenta configurar plugins em `tailwind.config.js` | Tailwind v4 usa configuração CSS nativa `@import "tailwindcss";` | Estilos não compilam |
| **Google GenAI** | Importa `import google.generativeai as genai` (legado) | SDK moderno é `from google import genai` (`client = genai.Client()`) | Falha silenciosa de autenticação e crash |
| **LangChain** | Importa tudo do pacote raiz `from langchain import ...` | LangChain 0.3+ separou em `langchain-core` e `langchain-community` | `ModuleNotFoundError` |
| **Flutter / Dart** | Usa `ThemeData.accentColor` e switches legados | Flutter 3.x / Material 3 adotou Dart 3 pattern matching e novas keys | Avisos de compilação ou falha de build |

### A Armadilha da Suposição Silenciosa
Agentes convencionais de "Vibe Coding" raramente leem `package.json`, `pyproject.toml` ou a documentação viva antes de gerar código. Eles supõem que sua memória interna é suficiente, forçando o desenvolvedor a passar horas fazendo "debugging fantasma".

---

## 2. A Solução KAIROS: A Doutrina Anti-Cutoff

O KAIROS institui a regra absoluta: **Nenhum agente tem permissão para adivinhar contratos de bibliotecas externas baseando-se apenas na memória de treinamento.**

Para resolver isso de ponta a ponta, introduzimos três componentes integrados:
1. **O Agente Especialista:** `kairos_scout` (The Technology Scout & Research Scientist).
2. **A Skill de Reconhecimento:** `skills/kairos-research/` (Upstream & Anti-Cutoff Protocol).
3. **O Scanner de Manifesto Nativo:** `kairos scout` no CLI do KAIROS.

```mermaid
flowchart TD
    Task["Nova Demanda (Modo Beta ou Gamma)"] --> Manifest["1. Manifest Reconnaissance (kairos scout)"]
    Manifest --> Scan["Identificação de Versões Exatas (package.json / pyproject.toml)"]
    
    Scan --> RiskCheck{"Pacote de Alto Risco de Cutoff?"}
    
    RiskCheck -->|Sim (Major Version Bump)| Scout["2. Invocação do kairos_scout (Research Scientist)"]
    RiskCheck -->|Não (Stack Estável)| Spec["Avançar para Delta Spec"]
    
    subgraph Research_Phase["Fase de Pesquisa Viva (kairos_scout)"]
        Scout --> LiveDoc["Consulta a Docs Vivas / MCP Docs / Web Search"]
        Scout --> TypeInspect["Leitura de .d.ts locais ou .pyi em node_modules"]
        Scout --> Output["Geração de research.md (Contratos e Diretivas Negativas)"]
    end
    
    Output --> Spec
    Spec --> Worker["3. kairos_worker (Implementa usando apenas APIs verificadas)"]
    Worker --> Auditor["4. kairos_auditor (Valida se diretivas negativas foram respeitadas)"]
```

---

## 3. O Protocolo de Pesquisa em 4 Etapas

Quando o subagente `kairos_scout` entra em ação, ele segue 4 passos verificáveis:

### Passo 1: Reconhecimento do Manifesto Local
Identifica a verdade concreta instalada no ambiente da máquina, inspecionando:
* Node: `package.json`, `package-lock.json`, `pnpm-lock.yaml`
* Python: `pyproject.toml`, `requirements.txt`, `poetry.lock`
* Flutter/Dart: `pubspec.yaml`, `pubspec.lock`
* Rust: `Cargo.toml`, `Cargo.lock`
* Go: `go.mod`, `go.sum`

### Passo 2: Avaliação de Risco de Breaking Changes
Compara as versões detectadas com a matriz de bibliotecas de alto risco. Se houver um salto de versão maior (ex: Next 13 -> 15 ou Pydantic 1 -> 2), o agente acende o alerta vermelho.

### Passo 3: Pesquisa Viva e Verificação de Tipos
O `kairos_scout`:
1. Utiliza ferramentas de pesquisa na web ou MCP de documentação (como `gemini-api-docs`, Developer Knowledge).
2. Abre e lê as definições de tipo locais (`.d.ts` ou `.pyi`) nos pacotes instalados.
3. Extrai as assinaturas exatas de funções, nomes de propriedades e tipos de retorno.

### Passo 4: Entrega do Brief de Pesquisa (`research.md`)
O cientista entrega um artefato formal na pasta da mudança ativa (`.kairos/changes/<id>/research.md`):

```markdown
# KAIROS Research Brief: modern-auth-feature

## 1. Verified Stack
| Package | Version | Cutoff Risk | Solution |
| :--- | :--- | :--- | :--- |
| @google/genai | 0.1.2 | CRITICAL | Use new `Client` syntax; old `GoogleGenerativeAI` class removed |

## 2. Verified Modern Method Signatures
```typescript
import { GoogleGenAI } from '@google/genai';
const ai = new GoogleGenAI({});
const response = await ai.models.generateContent({
  model: 'gemini-2.5-flash',
  contents: 'Hello world'
});
```

## 3. Negative Directives (O que o kairos_worker NÃO pode fazer)
- ❌ DO NOT import `from '@google/generative-ai'`
- ❌ DO NOT call `.getGenerativeModel()`
```

---

## 4. O Scanner Nativo do CLI: `kairos scout`

Para que o desenvolvedor ou o orquestrador identifique riscos imediatamente no terminal, criamos o comando `kairos scout`:

```bash
# Executar o scanner no projeto
python3 scripts/kairos_cli.py scout

# Ver todas as dependências indexadas
python3 scripts/kairos_cli.py scout --all

# Salvar o brief de pesquisa automaticamente na Delta Spec ativa
python3 scripts/kairos_cli.py scout --save-spec
```

### Exemplo de Saída do Terminal:
```text
=================================================================
🔭 KAIROS SCOUT: TECH STACK & ANTI-CUTOFF RECONNAISSANCE
=================================================================
📦 Manifests detected: package.json, pyproject.toml
📊 Total dependencies indexed: 24

🚨 HIGH KNOWLEDGE-CUTOFF RISKS DETECTED:
-----------------------------------------------------------------
  ⚠️  next (15.0.3) [from package.json]
     └─ Risk: App Router vs Pages Router, async headers in v15
  ⚠️  pydantic (2.9.2) [from pyproject.toml]
     └─ Risk: Breaking changes between v1 and v2 (.dict() removed, use .model_dump())
-----------------------------------------------------------------
💡 Directive for Agent:
   • Do NOT guess APIs for these packages based on training weights!
   • Run `kairos_scout` or verify method signatures in local types / live docs.
=================================================================
```

---

## 5. Governança pelo Dial Elástico: Protegendo os Tokens

Para não inflacionar o consumo de tokens com pesquisas desnecessárias, a doutrina é calibrada pelo **Dial Elástico**:

* **Modo Alpha (UI / Correções Cosméticas):**  
  *Pesquisa Externa Desativada.* Modificar uma cor, margem ou texto não exige consulta a documentações externas. Custo: **0 tokens**.
* **Modo Beta (Features Médias / Brownfield):**  
  *Scanner de Manifesto Automático.* Executa `kairos scout` para garantir que o agente não use dependências inexistentes.
* **Modo Gamma (Core Crítico / Novas Integrações de SDK):**  
  *Pesquisa Profunda Obrigatória.* O subagente `kairos_scout` é invocado para produzir o `research.md` antes da escrita de qualquer código de produção.

---

## 6. Conclusão

Com a adição do **`kairos_scout`** e da skill **`kairos-research`**, o KAIROS fecha a última grande brecha dos agentes autônomos: **a desatualização e alucinação de APIs externas**. O framework agora garante que o código gerado em 2026 seja nativo, moderno e compatível com as versões reais da sua máquina.
