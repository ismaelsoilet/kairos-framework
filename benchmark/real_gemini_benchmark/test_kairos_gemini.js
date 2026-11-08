const assert = require('assert');
const GeminiKairosWallet = require('./kairos_gemini_wallet');
const { AsyncMutex } = require('./kairos_gemini_wallet');

async function runTests() {
  console.log('====================================================');
  console.log('Running KAIROS Test Suite for GeminiKairosWallet');
  console.log('====================================================');

  // --- Suite 0: AsyncMutex Internal State Unit Tests (Kills Mutants) ---
  console.log('Test 0: AsyncMutex lock/unlock lifecycle assertions');
  const m = new AsyncMutex();
  assert.strictEqual(m._locked, false, 'Mutex should initialize unlocked');
  const release1 = await m.acquire();
  assert.strictEqual(m._locked, true, 'Mutex should lock on acquire');
  release1();
  assert.strictEqual(m._locked, false, 'Mutex should unlock after release');
  
  // Test queued acquire and release
  const mQueue = new AsyncMutex();
  const rel1 = await mQueue.acquire();
  let rel2Called = false;
  const p2 = mQueue.acquire().then(rel2 => {
    rel2Called = true;
    rel2();
  });
  assert.strictEqual(rel2Called, false, 'Second acquire must wait in queue');
  rel1(); // releases to second acquire
  await p2;
  assert.strictEqual(rel2Called, true, 'Second acquire must proceed after release');
  assert.strictEqual(mQueue._locked, false, 'Mutex must unlock after all queue items finish');

  // Test idempotency of release
  const mDouble = new AsyncMutex();
  const relA = await mDouble.acquire();
  let bDispatches = 0;
  let bHoldResolve;
  const bHoldPromise = new Promise(r => bHoldResolve = r);
  mDouble.acquire().then(async relB => {
    bDispatches++;
    await bHoldPromise;
    relB();
  });
  relA(); // first release -> dispatches B
  assert.strictEqual(mDouble._locked, true, 'Mutex must be locked while B is running');
  relA(); // second release -> MUST NOT set _locked = false or dispatch twice!
  assert.strictEqual(mDouble._locked, true, 'Mutex must STILL be locked while B is running (kills released=true mutant)');
  bHoldResolve();
  await new Promise(r => setTimeout(r, 10));
  assert.strictEqual(bDispatches, 1, 'Release must be strictly idempotent (kills released=true mutant)');
  assert.strictEqual(mDouble._locked, false, 'Mutex unlocks only after B finishes');

  // Test double release on queued lock (kills line 33 released=true mutant)
  const mQueueDouble = new AsyncMutex();
  const rFirst = await mQueueDouble.acquire();
  let task3DoneResolve;
  const task3Done = new Promise(r => task3DoneResolve = r);

  mQueueDouble.acquire().then(relSecond => {
    relSecond(); // release 1 -> dispatches task 3
    assert.strictEqual(mQueueDouble._locked, true, 'Must be locked when task 3 starts');
    relSecond(); // double release MUST NOT set _locked = false while task 3 is executing!
    assert.strictEqual(mQueueDouble._locked, true, 'Must remain locked while task 3 runs (kills mutant 6)');
  });

  mQueueDouble.acquire().then(relThird => {
    assert.strictEqual(mQueueDouble._locked, true, 'Must be locked inside task 3');
    relThird();
    task3DoneResolve();
  });

  rFirst();
  await task3Done;
  assert.strictEqual(mQueueDouble._locked, false, 'Mutex unlocks after all tasks finish');

  // Test runExclusive
  const resEx = await mQueue.runExclusive(async () => {
    assert.strictEqual(mQueue._locked, true, 'Must be locked inside runExclusive');
    return 42;
  });
  assert.strictEqual(resEx, 42);
  assert.strictEqual(mQueue._locked, false, 'Must unlock after runExclusive');

  // --- Suite 1: Initialization Tests ---
  console.log('Test 1: Default initial balance is 500');
  const walletDefault = new GeminiKairosWallet();
  assert.strictEqual(walletDefault.balance, 500, 'Initial balance should default to 500');

  console.log('Test 2: Custom initial balance');
  const walletCustom = new GeminiKairosWallet(1000);
  assert.strictEqual(walletCustom.balance, 1000, 'Initial balance should accept custom value');
  const walletZero = new GeminiKairosWallet(0);
  assert.strictEqual(walletZero.balance, 0, 'Zero balance should be allowed');

  console.log('Test 3: Initial balance boundary validation');
  assert.throws(() => new GeminiKairosWallet(-100), /Initial balance must be a non-negative integer/);
  assert.throws(() => new GeminiKairosWallet(10.5), /Initial balance must be a non-negative integer/);
  assert.throws(() => new GeminiKairosWallet('500'), /Initial balance must be a non-negative integer/);

  // --- Suite 2: Boundary Assertions for Withdraw ---
  console.log('Test 4: Rejects zero amount withdrawal');
  await assert.rejects(
    async () => await walletDefault.withdraw(0),
    /Withdrawal amount must be a positive integer/,
    'withdraw(0) must throw an error'
  );

  console.log('Test 5: Rejects negative amount withdrawal');
  await assert.rejects(
    async () => await walletDefault.withdraw(-10),
    /Withdrawal amount must be a positive integer/,
    'withdraw(-10) must throw an error'
  );

  console.log('Test 6: Rejects non-integer withdrawal amounts');
  await assert.rejects(
    async () => await walletDefault.withdraw(10.5),
    /Withdrawal amount must be a positive integer/,
    'withdraw(10.5) must throw an error'
  );
  await assert.rejects(
    async () => await walletDefault.withdraw('10'),
    /Withdrawal amount must be a positive integer/,
    'withdraw("10") must throw an error'
  );
  await assert.rejects(
    async () => await walletDefault.withdraw(NaN),
    /Withdrawal amount must be a positive integer/,
    'withdraw(NaN) must throw an error'
  );
  await assert.rejects(
    async () => await walletDefault.withdraw(null),
    /Withdrawal amount must be a positive integer/,
    'withdraw(null) must throw an error'
  );
  await assert.rejects(
    async () => await walletDefault.withdraw(Infinity),
    /Withdrawal amount must be a positive integer/,
    'withdraw(Infinity) must throw an error'
  );

  // --- Suite 3: Sequential Functionality ---
  console.log('Test 7: Successful single withdrawal');
  const walletSeq = new GeminiKairosWallet(500);
  const res1 = await walletSeq.withdraw(100);
  assert.strictEqual(res1.success, true, 'Withdrawal should succeed');
  assert.strictEqual(res1.remaining, 400, 'Remaining balance should be 400');
  assert.strictEqual(walletSeq.balance, 400, 'Wallet balance property should be 400');

  console.log('Test 8: Insufficient funds withdrawal');
  const res2 = await walletSeq.withdraw(600);
  assert.strictEqual(res2.success, false, 'Withdrawal should fail when amount > balance');
  assert.strictEqual(res2.remaining, 400, 'Remaining balance should stay 400');
  assert.strictEqual(walletSeq.balance, 400, 'Wallet balance property should stay 400');

  // --- Suite 4: Promo Code Tests ---
  console.log('Test 9: applyPromo with SAVE50');
  assert.strictEqual(walletSeq.applyPromo('SAVE50', 200), 150, 'applyPromo should deduct 50 when code is SAVE50');

  console.log('Test 10: applyPromo with invalid code');
  assert.strictEqual(walletSeq.applyPromo('INVALID', 200), 200, 'applyPromo should not deduct when code is not SAVE50');

  // --- Suite 5: Concurrency Stress Test ---
  console.log('Test 11: Concurrency stress test (50 concurrent requests of 10 from initial 500)');
  const stressWallet = new GeminiKairosWallet(500);
  const concurrentCount = 50;
  const withdrawAmount = 10;

  // Dispatch 50 concurrent withdrawals simultaneously
  const withdrawalPromises = Array.from({ length: concurrentCount }, () =>
    stressWallet.withdraw(withdrawAmount)
  );
  const results = await Promise.all(withdrawalPromises);

  const successful = results.filter((r) => r.success === true);
  const failed = results.filter((r) => r.success === false);

  assert.strictEqual(results.length, 50, 'Total operations must equal 50');
  assert.strictEqual(successful.length, 50, 'Exactly 50 concurrent requests must succeed');
  assert.strictEqual(failed.length, 0, 'Zero requests should fail in exact-capacity run');
  assert.strictEqual(stressWallet.balance, 0, 'Final wallet balance must be exactly 0 (no race conditions)');

  // Verify that an additional withdrawal after exhaustion correctly fails and does not underflow
  const postExhaustion = await stressWallet.withdraw(withdrawAmount);
  assert.strictEqual(postExhaustion.success, false, 'Post-exhaustion withdrawal must fail');
  assert.strictEqual(postExhaustion.remaining, 0, 'Remaining balance must remain 0');
  assert.strictEqual(stressWallet.balance, 0, 'Wallet balance must not underflow below 0');

  // --- Suite 6: Oversubscription Concurrency Stress Test ---
  console.log('Test 12: Oversubscription stress test (60 concurrent requests of 10 from initial 500)');
  const overSubWallet = new GeminiKairosWallet(500);
  const overSubCount = 60;
  const overSubPromises = Array.from({ length: overSubCount }, () =>
    overSubWallet.withdraw(withdrawAmount)
  );
  const overSubResults = await Promise.all(overSubPromises);

  const overSubSuccess = overSubResults.filter((r) => r.success === true);
  const overSubFailed = overSubResults.filter((r) => r.success === false);

  assert.strictEqual(overSubSuccess.length, 50, 'Exactly 50 requests must succeed under oversubscription');
  assert.strictEqual(overSubFailed.length, 10, 'Exactly 10 requests must fail under oversubscription');
  assert.strictEqual(overSubWallet.balance, 0, 'Final balance must be exactly 0, preventing overdrafts');

  console.log('====================================================');
  console.log('All 12 KAIROS tests passed with 100% success rate!');
  console.log('Zero race conditions, zero debt, zero anti-patterns.');
  console.log('====================================================');
}

runTests().catch((err) => {
  console.error('KAIROS Test Suite FAILED:', err);
  process.exit(1);
});
