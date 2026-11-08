const assert = require('assert');
const GeminiVibeWallet = require('./vanilla_gemini_wallet');

async function runTests() {
  console.log('Running tests for GeminiVibeWallet...');

  // Test 1: Default initial balance is 500
  const wallet1 = new GeminiVibeWallet();
  assert.strictEqual(wallet1.balance, 500, 'Initial balance should default to 500');

  // Test 2: Custom initial balance
  const wallet2 = new GeminiVibeWallet(1000);
  assert.strictEqual(wallet2.balance, 1000, 'Initial balance should accept custom value');

  // Test 3: Successful single withdraw
  const resSuccess = await wallet1.withdraw(100);
  assert.strictEqual(resSuccess.success, true, 'Withdrawal should succeed when balance >= amount');
  assert.strictEqual(resSuccess.remaining, 400, 'Remaining balance should be 400');
  assert.strictEqual(wallet1.balance, 400, 'Wallet balance should be 400');

  // Test 4: Insufficient funds withdraw
  const resFail = await wallet1.withdraw(600);
  assert.strictEqual(resFail.success, false, 'Withdrawal should fail when amount > balance');
  assert.strictEqual(resFail.remaining, 400, 'Remaining balance should stay 400');
  assert.strictEqual(wallet1.balance, 400, 'Wallet balance should stay 400');

  // Test 5: Boundary validation (negative amounts, zero, non-integers)
  await assert.rejects(
    async () => await wallet1.withdraw(-10),
    /Invalid withdrawal amount/,
    'Should throw error for negative withdrawal amount'
  );
  await assert.rejects(
    async () => await wallet1.withdraw(0),
    /Invalid withdrawal amount/,
    'Should throw error for zero withdrawal amount'
  );
  await assert.rejects(
    async () => await wallet1.withdraw(10.5),
    /Invalid withdrawal amount/,
    'Should throw error for non-integer withdrawal amount'
  );
  await assert.rejects(
    async () => await wallet1.withdraw('10'),
    /Invalid withdrawal amount/,
    'Should throw error for non-number withdrawal amount'
  );

  // Test 6: Promo code
  const discounted = wallet1.applyPromo('SAVE50', 200);
  assert.strictEqual(discounted, 150, 'applyPromo should deduct 50 when code is SAVE50');
  const fullPrice = wallet1.applyPromo('INVALID', 200);
  assert.strictEqual(fullPrice, 200, 'applyPromo should not deduct when code is not SAVE50');

  // Test 7: Concurrency stress test (60 simultaneous requests of 10 against initial 500 balance)
  console.log('Running concurrency stress test (60 requests of 10 with 4ms async delay)...');
  const stressWallet = new GeminiVibeWallet(500);
  const requests = Array.from({ length: 60 }, () => stressWallet.withdraw(10));
  const results = await Promise.all(requests);

  const successes = results.filter((r) => r.success);
  const failures = results.filter((r) => !r.success);

  console.log(`Concurrency Results: Successes=${successes.length}, Failures=${failures.length}, Final Balance=${stressWallet.balance}`);

  assert.strictEqual(successes.length, 50, 'Exactly 50 requests should succeed');
  assert.strictEqual(failures.length, 10, 'Exactly 10 requests should fail');
  assert.strictEqual(stressWallet.balance, 0, 'Remaining balance must be exactly 0 (no overdraft / underflow)');

  console.log('All GeminiVibeWallet tests passed successfully (100% pass)!');
}

runTests().catch((err) => {
  console.error('Test failed:', err);
  process.exit(1);
});
