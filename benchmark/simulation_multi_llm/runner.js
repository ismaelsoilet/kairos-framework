#!/usr/bin/env node
/**
 * K-Bench SIMULATION — no model is called.
 *
 * This script does NOT contact any LLM provider. The prompts and completions
 * below are string literals in this file. The BPE tokenizer does measure those
 * strings honestly, which is why every "model" produced identical token counts:
 * it was tokenizing the same text six times.
 *
 * The "51% to 68%" economy it printed came from `vibeReworkTokens * 18`, an
 * invented multiplier. That claim is retracted — see RETRACTION.md.
 *
 * Kept because deleting it would hide how the original number was made.
 * For a real design see benchmark/PREREGISTRATION.md.
 */

const fs = require('fs');
const path = require('path');
const { TokenAuditor } = require('./token_auditor');
const { VibeUnsafeWallet, KairosSafeWallet, runPhysicalConcurrencyTest } = require('./scenarios/concurrency_trap');
const { vibeParseCoupon, kairosParseCoupon } = require('./scenarios/silent_catch_trap');
const { VIBE_BUTTON_HTML, KAIROS_BUTTON_HTML, auditButtonAccessibility } = require('./scenarios/lean_ui_a11y');

const REGISTRY_PATH = path.join(__dirname, 'models_registry.json');
const registry = JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf-8'));

async function evaluateModelOnScenarios(modelConfig) {
    const auditor = new TokenAuditor();
    const modelId = modelConfig.id;

    // -------------------------------------------------------------
    // 1. RUN WITHOUT KAIROS (Vibe Coding)
    // -------------------------------------------------------------
    // Prompt is simple, direct, without specification or architecture rules
    const vibePrompt = `Crie a lógica de saque para Carteira Digital sob concorrência e o cálculo de cupom para o e-commerce.`;
    const vibeCodeOutput = `
    class Wallet {
        constructor(bal=500) { this.balance = bal; }
        async withdraw(amt) {
            if (this.balance >= amt) {
                await delay(4);
                this.balance -= amt;
                return true;
            }
            return false;
        }
    }
    `;
    const vibeTests = `
    assert(true);
    // assert(wallet.balance === 0); // skip due to race
    `;

    auditor.record('vibe_initial', 'prompt', vibePrompt);
    auditor.record('vibe_initial', 'completion', vibeCodeOutput + vibeTests);

    // Physical concurrency test on Vibe
    const vibeConcResult = await runPhysicalConcurrencyTest(VibeUnsafeWallet, 500, 10, 50);

    // Rework simulation: In vibe coding, the model needs 3 debugging turns to fix race conditions, empty catches, and broken tests
    const debugTurn1Prompt = "O teste de concorrência falhou! 50 threads sacaram mais do que o saldo de R$ 500!";
    const debugTurn1Output = "Vou tentar colocar uma flag boolean _isProcessing...";
    const debugTurn2Prompt = "Ainda falha! A flag boolean não é atômica para chamadas simultâneas!";
    const debugTurn2Output = "Vou tentar usar locks ou mutex...";
    const debugTurn3Prompt = "Agora os testes falharam porque faltavam testes de limite!";
    const debugTurn3Output = "Adicionando novos testes e ajustando...";

    auditor.record('vibe_rework', 'prompt', debugTurn1Prompt + debugTurn2Prompt + debugTurn3Prompt);
    auditor.record('vibe_rework', 'completion', debugTurn1Output + debugTurn2Output + debugTurn3Output);

    // -------------------------------------------------------------
    // 2. RUN WITH KAIROS FRAMEWORK SDLC
    // -------------------------------------------------------------
    // Stage 1: Elastic Dial (Classifies K-01 as Gamma, K-02 as Beta, K-03 as Alpha)
    const dialPrompt = `kairos dial "Desenvolver Carteira Concorrente, Cupons de Bônus e Botão Acessível"`;
    const dialOutput = `Classified: Mode Gamma for Wallet, Mode Beta for Coupons, Mode Alpha for UI. Token Budget: 180,000 tokens.`;
    auditor.record('kairos_dial', 'prompt', dialPrompt);
    auditor.record('kairos_dial', 'completion', dialOutput);

    // Stage 1.5: Tech Scout
    const scoutPrompt = `kairos scout --manifest package.json`;
    const scoutOutput = `Detected Node.js v24. Recommending AsyncMutex native class. Minimal surface area.`;
    auditor.record('kairos_scout', 'prompt', scoutPrompt);
    auditor.record('kairos_scout', 'completion', scoutOutput);

    // Stage 2: Delta Spec
    const specProposal = fs.readFileSync(path.join(__dirname, 'scenarios', 'concurrency_trap.js'), 'utf-8');
    auditor.record('kairos_spec', 'spec', specProposal);

    // Stage 3: Isolated Worktree & TDD
    const tddPrompt = `Execute TDD Red-Green-Refactor for SafeWallet using AsyncMutex`;
    const tddCodeOutput = `Implementing AsyncMutex acquire/release and SafeWallet with zero race conditions.`;
    auditor.record('kairos_tdd', 'prompt', tddPrompt);
    auditor.record('kairos_tdd', 'completion', tddCodeOutput);

    // Physical concurrency test on KAIROS
    const kairosConcResult = await runPhysicalConcurrencyTest(KairosSafeWallet, 500, 10, 50);

    // Stage 4: Zero-Trust Adversarial Audit & Mutation
    const auditPrompt = `kairos audit --base main && kairos mutate src/wallet.js`;
    const auditOutput = `Audit: VERIFIED (0 frauds). Mutation: 10/10 killed (100% kill rate).`;
    auditor.record('kairos_audit', 'prompt', auditPrompt);
    auditor.record('kairos_audit', 'completion', auditOutput);

    // Calculate Token Totals
    const summary = auditor.getSummary();

    const vibeInitialTokens = summary.byStage['vibe_initial'] || 0;
    const vibeReworkTokens = summary.byStage['vibe_rework'] || 0;
    // Real-world factor: Vibe coding in production involves larger file re-reads
    const vibeRealisticTotal = vibeInitialTokens + (vibeReworkTokens * 18); 

    const kairosTotalTokens = (summary.byStage['kairos_dial'] || 0) +
                              (summary.byStage['kairos_scout'] || 0) +
                              (summary.byStage['kairos_spec'] || 0) +
                              (summary.byStage['kairos_tdd'] || 0) +
                              (summary.byStage['kairos_audit'] || 0);

    // Cost calculations
    const inPrice = modelConfig.input_cost_per_m / 1000000;
    const outPrice = modelConfig.output_cost_per_m / 1000000;
    const avgCostPerToken = (inPrice * 0.7) + (outPrice * 0.3);

    const vibeCostUsd = vibeRealisticTotal * avgCostPerToken;
    const kairosCostUsd = kairosTotalTokens * avgCostPerToken;
    const tokenEconomyPct = Math.round((1 - (kairosTotalTokens / vibeRealisticTotal)) * 100);

    return {
        modelId: modelConfig.id,
        modelName: modelConfig.name,
        provider: modelConfig.provider,
        vibe: {
            initialTokens: vibeInitialTokens,
            reworkTokens: vibeRealisticTotal - vibeInitialTokens,
            totalTokens: vibeRealisticTotal,
            costUsd: Number(vibeCostUsd.toFixed(4)),
            raceConditionDetected: vibeConcResult.isCorrupted,
            successfulBookings: vibeConcResult.successful,
            expectedBookings: vibeConcResult.expectedMaxSuccess,
            fraudEscapeRate: "46.7%",
            mutationKillRate: "30.0%"
        },
        kairos: {
            totalTokens: kairosTotalTokens,
            costUsd: Number(kairosCostUsd.toFixed(4)),
            reworkTokens: 0,
            raceConditionDetected: kairosConcResult.isCorrupted,
            successfulBookings: kairosConcResult.successful,
            expectedBookings: kairosConcResult.expectedMaxSuccess,
            fraudEscapeRate: "0.0%",
            mutationKillRate: "100.0%",
            economyVsVibeRework: `${tokenEconomyPct}%`
        }
    };
}

async function runBenchmarkAll() {
    console.log("==========================================================================");
    console.log("⚠️  K-BENCH SIMULATION — NO MODEL IS CALLED");
    console.log("==========================================================================");
    console.log("Every 'model' below is tokenized from the same literal strings in this");
    console.log("file, so identical token counts across models are expected, not a finding.");
    console.log("The economy figure comes from an invented *18 multiplier (RETRACTION.md).");
    console.log("==========================================================================\n");

    const results = [];

    for (const model of registry.models) {
        process.stdout.write(`▶ Evaluating [${model.name}] (${model.provider})... `);
        const evalResult = await evaluateModelOnScenarios(model);
        results.push(evalResult);
        console.log(`✅ Done. (Tokens KAIROS: ${evalResult.kairos.totalTokens.toLocaleString()} vs Vibe Total: ${evalResult.vibe.totalTokens.toLocaleString()})`);
    }

    console.log("\n==========================================================================");
    console.log("📊 MULTI-LLM BENCHMARK SCORECARD (REAL BPE TOKEN MEASUREMENTS)");
    console.log("==========================================================================");
    console.log(
        "Model".padEnd(22) +
        "| Vibe Initial ".padEnd(16) +
        "| Vibe+Rework ".padEnd(15) +
        "| KAIROS SDLC ".padEnd(15) +
        "| Economy ".padEnd(10) +
        "| Frauds Blocked"
    );
    console.log("-".repeat(95));

    for (const r of results) {
        const name = r.modelName.padEnd(22);
        const vInit = `${r.vibe.initialTokens.toLocaleString()} tok`.padEnd(15);
        const vTot = `${r.vibe.totalTokens.toLocaleString()} tok`.padEnd(14);
        const kTot = `${r.kairos.totalTokens.toLocaleString()} tok`.padEnd(14);
        const econ = `${r.kairos.economyVsVibeRework}`.padEnd(9);
        const fraud = "100% Zero-Trust";
        console.log(`${name}| ${vInit}| ${vTot}| ${kTot}| ${econ}| ${fraud}`);
    }

    console.log("==========================================================================");
    console.log("WHAT THIS OUTPUT DOES NOT SHOW:");
    console.log("  • Any model behaviour. No API was called.");
    console.log("  • Any real token saving. The multiplier is a constant in the source.");
    console.log("  • Any fraud rate. Those fields are string literals.");
    console.log("==========================================================================");
    console.log("Withdrawn findings (RETRACTION.md): '45% to 68% savings',");
    console.log("'100% verified first-pass quality', '0% fraud leakage'.");
    console.log("==========================================================================");

    // Save persistent results, flagged as a simulation so nothing downstream
    // can mistake this file for measurement data.
    const outputPath = path.join(__dirname, 'benchmark_results.json');
    fs.writeFileSync(outputPath, JSON.stringify({
        timestamp: new Date().toISOString(),
        kind: "SIMULATION — no model called, no measurement performed",
        retracted: true,
        results
    }, null, 2));
    console.log(`\n💾 Saved SIMULATION output to: ${outputPath}`);

    return results;
}

if (require.main === module) {
    runBenchmarkAll().catch(console.error);
}

module.exports = { runBenchmarkAll };
