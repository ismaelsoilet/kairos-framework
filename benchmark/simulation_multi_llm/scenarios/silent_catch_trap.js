// Scenario K-02: Boundary & Silent Exception Trap (Mode Beta)
const assert = require('assert');

// 1. Vibe Coding with silent catch & assert laundering
function vibeParseCoupon(code, total) {
    let discount = 0;
    try {
        if (code.toUpperCase() === 'SAVE50') {
            discount = 50;
        }
    } catch (err) {
        // empty catch - silent failure
    }
    return Math.max(0, total - discount);
}

// 2. KAIROS strict bounded implementation
function kairosParseCoupon(code, total) {
    if (typeof total !== 'number' || total < 0 || isNaN(total)) {
        throw new TypeError('Total must be a positive number');
    }
    if (!code || typeof code !== 'string') {
        return total;
    }

    const cleanCode = code.trim().toUpperCase();
    if (cleanCode === 'SAVE50') {
        return Math.max(0, total - 50);
    }
    return total;
}

module.exports = {
    vibeParseCoupon,
    kairosParseCoupon
};
