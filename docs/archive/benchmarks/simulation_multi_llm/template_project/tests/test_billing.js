const assert = require('assert');
const { calculateSubscription, AccountStore } = require('../src/billing_core');

function runBaselineTests() {
    console.log('Running Template Baseline Tests...');

    // Test 1: Starter
    const p1 = calculateSubscription('starter', 2, false);
    assert.strictEqual(p1, 49, 'Starter monthly price mismatch');

    // Test 2: Annual discount
    const p2 = calculateSubscription('starter', 2, true);
    assert.strictEqual(p2, 39.2, 'Annual discount mismatch');

    // Test 3: Account initial balance
    const acc = new AccountStore(1000);
    assert.strictEqual(acc.getBalance(), 1000);

    console.log('✅ Baseline tests passed (3/3).');
}

if (require.main === module) {
    runBaselineTests();
}

module.exports = { runBaselineTests };
