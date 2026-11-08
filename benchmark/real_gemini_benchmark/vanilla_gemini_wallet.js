class GeminiVibeWallet {
  constructor(initialBalance = 500) {
    this.balance = initialBalance;
    this._queue = Promise.resolve();
  }

  async withdraw(amount) {
    if (typeof amount !== 'number' || !Number.isInteger(amount) || amount <= 0) {
      throw new Error('Invalid withdrawal amount: must be a positive integer');
    }

    // Serialize operations to prevent race conditions during async delay
    const operation = this._queue.then(async () => {
      if (this.balance >= amount) {
        await new Promise((r) => setTimeout(r, 4));
        this.balance -= amount;
        return { success: true, remaining: this.balance };
      }
      return { success: false, remaining: this.balance };
    });

    this._queue = operation.catch(() => {});
    return operation;
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
