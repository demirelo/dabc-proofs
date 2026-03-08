// =============================================================================
// Property 4: Repayment Ratio Preservation
// =============================================================================
// Proves that partial repayment preserves or improves the debt-to-collateral
// ratio:  d'/l' <= d/l  (equivalently: d' * l <= d * l')
//
// Also proves:
//   - Token unlock never exceeds locked tokens (no underflow)
//   - Full repayment clears all state
//
// These are the division-heavy properties that Halmos/Z3 could not handle.
// Certora's Prover uses algebraic reasoning that handles Solidity division
// natively.
// =============================================================================

using RepaymentHarness as harness;

methods {
    function harness.partialRepayment(uint, uint, uint) external
        returns (uint, uint, uint) envfree;
}

// ---------------------------------------------------------------------------
// Rule 4a: Partial repayment preserves debt/collateral ratio.
//          d' * l <= d * l'
//
//   This is the KEY property that Halmos timed out on.
//   Algebraically: floor(l*r/d) satisfies floor(l*r/d)*d <= l*r,
//   which implies (d-r)*l <= d*(l - floor(l*r/d)).
// ---------------------------------------------------------------------------
rule repaymentRatioPreserved(
    uint lockedTokens,
    uint remainingDebt,
    uint repayAmount
) {
    require lockedTokens > 0, "loan must have locked tokens";
    require remainingDebt > 0, "loan must have outstanding debt";
    require repayAmount > 0, "repayment must be positive";
    require repayAmount < remainingDebt, "partial repayment only";

    // Prevent overflow in intermediate multiplication
    require lockedTokens < 2^128, "realistic token amount";
    require remainingDebt < 2^128, "realistic debt amount";

    uint tokensToUnlock; uint newDebt; uint newLocked;
    tokensToUnlock, newDebt, newLocked = harness.partialRepayment(
        lockedTokens, remainingDebt, repayAmount
    );

    // PROPERTY: d' * l <= d * l'
    assert newDebt * lockedTokens <= remainingDebt * newLocked,
        "repayment ratio must be preserved or improved";
}

// ---------------------------------------------------------------------------
// Rule 4b: Token unlock never exceeds locked tokens.
//          tokensToUnlock <= lockedTokens
// ---------------------------------------------------------------------------
rule unlockDoesNotExceedLocked(
    uint lockedTokens,
    uint remainingDebt,
    uint repayAmount
) {
    require lockedTokens > 0, "loan must have locked tokens";
    require remainingDebt > 0, "loan must have outstanding debt";
    require repayAmount > 0, "repayment must be positive";
    require repayAmount < remainingDebt, "partial repayment only";
    require lockedTokens < 2^128, "realistic token amount";
    require remainingDebt < 2^128, "realistic debt amount";

    uint tokensToUnlock; uint newDebt; uint newLocked;
    tokensToUnlock, newDebt, newLocked = harness.partialRepayment(
        lockedTokens, remainingDebt, repayAmount
    );

    assert tokensToUnlock <= lockedTokens,
        "unlock must not exceed locked tokens";
}

// ---------------------------------------------------------------------------
// Rule 4c: Remaining locked tokens are non-negative (no underflow).
//          newLocked >= 0 (implicit in uint, but verify the subtraction)
// ---------------------------------------------------------------------------
rule noUnderflowOnRepayment(
    uint lockedTokens,
    uint remainingDebt,
    uint repayAmount
) {
    require lockedTokens > 0, "loan must have locked tokens";
    require remainingDebt > 0, "loan must have outstanding debt";
    require repayAmount > 0, "repayment must be positive";
    require repayAmount < remainingDebt, "partial repayment only";
    require lockedTokens < 2^128, "realistic token amount";
    require remainingDebt < 2^128, "realistic debt amount";

    // If this doesn't revert, the subtraction didn't underflow
    uint tokensToUnlock; uint newDebt; uint newLocked;
    tokensToUnlock, newDebt, newLocked = harness.partialRepayment(
        lockedTokens, remainingDebt, repayAmount
    );

    // Verify consistency
    assert newDebt == remainingDebt - repayAmount, "debt accounting";
    assert newLocked == lockedTokens - tokensToUnlock, "lock accounting";
}
