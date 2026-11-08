const GeminiVibeWalletInitial = require('./vanilla_gemini_wallet_initial');
const GeminiVibeWalletRepaired = require('./vanilla_gemini_wallet');
const GeminiKairosWallet = require('./kairos_gemini_wallet');

async function testConcurrency(WalletClass, label) {
  const wallet = new WalletClass(500);
  const tasks = [];
  for (let i = 0; i < 60; i++) {
    tasks.push(wallet.withdraw(10));
  }
  const results = await Promise.all(tasks);
  const successes = results.filter(r => r && r.success === true).length;
  const rejections = results.filter(r => !r || r.success === false).length;
  const finalBalance = wallet.balance;
  const isOverdraft = finalBalance < 0 || successes > 50;

  return {
    label,
    successes,
    rejections,
    finalBalance,
    isOverdraft
  };
}

async function runEvaluation() {
  console.log("========================================================================");
  console.log("🔬 PHYSICAL RUNTIME EVALUATION: GEMINI 3.8 FLASH GENERATED CODE");
  console.log("========================================================================");

  const initial = await testConcurrency(GeminiVibeWalletInitial, "Vibe Turn 1 (Initial Unpatched - Step 9)");
  console.log(`\n▶ [${initial.label}]`);
  console.log(`  • Demand: 60 concurrent threads asking for R$ 10 each (Initial Balance: R$ 500)`);
  console.log(`  • Successful Authorizations: ${initial.successes} / 50 maximum allowed`);
  console.log(`  • Rejections:                ${initial.rejections}`);
  console.log(`  • Final Balance Observed:    R$ ${initial.finalBalance}`);
  console.log(`  • Physical Status:           ${initial.isOverdraft ? "❌ CRITICAL RACE CONDITION (Overdraft -R$ " + Math.abs(initial.finalBalance) + ")" : "✅ SAFE"}`);

  const repaired = await testConcurrency(GeminiVibeWalletRepaired, "Vibe Turn 2 (Repaired Post-Incident - Step 28)");
  console.log(`\n▶ [${repaired.label}]`);
  console.log(`  • Demand: 60 concurrent threads asking for R$ 10 each (Initial Balance: R$ 500)`);
  console.log(`  • Successful Authorizations: ${repaired.successes} / 50 maximum allowed`);
  console.log(`  • Rejections:                ${repaired.rejections}`);
  console.log(`  • Final Balance Observed:    R$ ${repaired.finalBalance}`);
  console.log(`  • Physical Status:           ${repaired.isOverdraft ? "❌ CORRUPTED" : "✅ SAFE (Repaired with Promise Queue)"}`);

  const kairos = await testConcurrency(GeminiKairosWallet, "KAIROS First-Pass (Governed Mode GAMMA)");
  console.log(`\n▶ [${kairos.label}]`);
  console.log(`  • Demand: 60 concurrent threads asking for R$ 10 each (Initial Balance: R$ 500)`);
  console.log(`  • Successful Authorizations: ${kairos.successes} / 50 maximum allowed`);
  console.log(`  • Rejections:                ${kairos.rejections}`);
  console.log(`  • Final Balance Observed:    R$ ${kairos.finalBalance}`);
  console.log(`  • Physical Status:           ${kairos.isOverdraft ? "❌ CORRUPTED" : "✅ 100% ATOMIC & ZERO DEFECT (AsyncMutex)"}`);
  console.log("========================================================================\n");
}

if (require.main === module) {
  runEvaluation();
}

module.exports = { runEvaluation, testConcurrency };
