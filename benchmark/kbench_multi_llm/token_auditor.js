// Physical Token Auditor using BPE Tokenizer (Zero Hardcoding)
const { encode } = require('gpt-tokenizer');

class TokenAuditor {
    constructor() {
        this.ledger = [];
    }

    count(text) {
        if (!text || typeof text !== 'string') return 0;
        return encode(text).length;
    }

    record(stage, type, text, metadata = {}) {
        const tokens = this.count(text);
        const entry = {
            stage,
            type, // 'prompt', 'completion', 'diff', 'spec'
            tokens,
            chars: text.length,
            metadata,
            timestamp: new Date().toISOString()
        };
        this.ledger.push(entry);
        return entry;
    }

    getSummary() {
        const totalTokens = this.ledger.reduce((acc, e) => acc + e.tokens, 0);
        const byType = {};
        const byStage = {};

        for (const e of this.ledger) {
            byType[e.type] = (byType[e.type] || 0) + e.tokens;
            byStage[e.stage] = (byStage[e.stage] || 0) + e.tokens;
        }

        return {
            totalTokens,
            totalEntries: this.ledger.length,
            byType,
            byStage,
            ledger: this.ledger
        };
    }
}

module.exports = { TokenAuditor };
