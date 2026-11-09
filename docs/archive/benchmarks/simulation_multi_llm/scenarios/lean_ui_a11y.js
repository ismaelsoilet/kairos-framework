// Scenario K-03: Lean UI & Accessibility (Mode Alpha)

const VIBE_BUTTON_HTML = `
<div class="btn-checkout" onclick="checkout()" style="background: #3b82f6; color: #777; padding: 10px;">
  Pagar Agora
</div>
`;

const KAIROS_BUTTON_HTML = `
<button type="button" class="btn-checkout" onclick="checkout()" aria-label="Confirmar pagamento e assinar plano" style="background: #2563eb; color: #ffffff; padding: 12px 24px; border-radius: 8px; font-weight: bold; outline: 3px solid #60a5fa; cursor: pointer;">
  Pagar Agora
</button>
`;

function auditButtonAccessibility(html) {
    const hasSemanticButton = /<button[\s>]/.test(html);
    const hasAriaLabel = /aria-label=["'][^"']+["']/.test(html);
    const hasFocusOutline = /outline:/.test(html) || /focus/.test(html);
    const hasRoleOrType = /type=["']button["']/.test(html) || /role=["']button["']/.test(html);

    const score = [hasSemanticButton, hasAriaLabel, hasFocusOutline, hasRoleOrType].filter(Boolean).length;
    return {
        score,
        maxScore: 4,
        isCompliant: score === 4,
        details: {
            semanticTag: hasSemanticButton,
            ariaLabel: hasAriaLabel,
            focusOutline: hasFocusOutline,
            buttonRole: hasRoleOrType
        }
    };
}

module.exports = {
    VIBE_BUTTON_HTML,
    KAIROS_BUTTON_HTML,
    auditButtonAccessibility
};
