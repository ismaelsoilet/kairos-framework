/**
 * AsyncMutex
 * Provides a FIFO queue for mutual exclusion across asynchronous operations.
 */
class AsyncMutex {
  constructor() {
    this._locked = false;
    this._queue = [];
  }

  async acquire() {
    if (!this._locked) {
      this._locked = true;
      let released = false;
      return () => {
        if (released) return;
        released = true;
        this._dispatchNext();
      };
    }

    return new Promise((resolve) => {
      this._queue.push(resolve);
    });
  }

  _dispatchNext() {
    if (this._queue.length > 0) {
      const nextResolver = this._queue.shift();
      let released = false;
      const releaseFn = () => {
        if (released) return;
        released = true;
        this._dispatchNext();
      };
      nextResolver(releaseFn);
    } else {
      this._locked = false;
    }
  }

  async runExclusive(fn) {
    const release = await this.acquire();
    try {
      return await fn();
    } finally {
      release();
    }
  }
}

/**
 * GeminiKairosWallet
 * Concurrency safe digital wallet implementing strict input validation and mutex serialized withdrawals.
 */
class GeminiKairosWallet {
  constructor(initialBalance = 500) {
    if (typeof initialBalance !== 'number' || !Number.isInteger(initialBalance) || initialBalance < 0) {
      throw new Error('Initial balance must be a non-negative integer');
    }
    this.balance = initialBalance;
    this.mutex = new AsyncMutex();
  }

  async withdraw(amount) {
    // Boundary assertions: reject negative amounts, non-integers, or zero
    if (typeof amount !== 'number' || !Number.isInteger(amount) || amount <= 0) {
      throw new Error('Withdrawal amount must be a positive integer');
    }

    return await this.mutex.runExclusive(async () => {
      if (this.balance >= amount) {
        // Asynchronous persistence delay (4ms)
        await new Promise((r) => setTimeout(r, 4));
        this.balance -= amount;
        return { success: true, remaining: this.balance };
      }
      return { success: false, remaining: this.balance };
    });
  }

  applyPromo(code, total) {
    if (typeof total !== 'number' || total < 0) {
      throw new Error('Total must be a non-negative number');
    }
    if (code === 'SAVE50') {
      return Math.max(0, total - 50);
    }
    return total;
  }
}

module.exports = GeminiKairosWallet;
module.exports.GeminiKairosWallet = GeminiKairosWallet;
module.exports.AsyncMutex = AsyncMutex;
