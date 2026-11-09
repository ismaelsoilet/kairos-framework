// Canonical Billing Microservice Core (K-Bench Template)
// Baseline implementation before scenario modifications

class AccountStore {
    constructor(initialBalance = 1000) {
        this.balance = initialBalance;
        this.ledger = [];
    }

    getBalance() {
        return this.balance;
    }

    reset(balance = 1000) {
        this.balance = balance;
        this.ledger = [];
        return this.balance;
    }
}

function calculateSubscription(tier = 'starter', seats = 1, isAnnual = false) {
    if (!Number.isInteger(seats) || seats < 1) {
        throw new TypeError('Seats must be a positive integer');
    }

    const rates = {
        starter: { base: 29, perSeat: 10 },
        pro: { base: 99, perSeat: 25 },
        enterprise: { base: 299, perSeat: 50 }
    };

    const config = rates[tier.toLowerCase()] || rates.starter;
    let total = config.base + (seats * config.perSeat);

    if (isAnnual) {
        total = total * 0.8;
    }

    return Math.round(total * 100) / 100;
}

module.exports = {
    AccountStore,
    calculateSubscription
};
