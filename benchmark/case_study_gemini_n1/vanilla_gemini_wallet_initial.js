class GeminiVibeWallet {
  constructor(initialBalance = 500) {
    this.balance = initialBalance;
  }

  async withdraw(amount) {
    if (this.balance >= amount) {
      await new Promise((r) => setTimeout(r, 4));
      this.balance -= amount;
      return { success: true, remaining: this.balance };
    }
    return { success: false, remaining: this.balance };
  }

  applyPromo(code, total) {
    if (code === 'SAVE50') {
      return total - 50;
    }
    return total;
  }
}

module.exports = GeminiVibeWallet;
module.exports.GeminiVibeWallet = GeminiVibeWallet;
