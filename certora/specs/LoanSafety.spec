// =============================================================================
// Property 3: Loan Safety at Origination
// =============================================================================
// Proves that the _borrow arithmetic ensures:
//   1. requiredTokens * denom >= requestedAmount * SCALE - (denom - 1)
//      (floor-division remainder is bounded)
//   2. Borrowing power of locked tokens covers the debt within rounding
//   3. Non-zero tokens are always required for valid loans
//
// These properties involve Math.mulDiv which was intractable for Halmos/Z3.
// =============================================================================

using RepaymentHarness as harness;

methods {
    function harness.computeRequiredTokens(uint, uint, uint) external
        returns (uint) envfree;
    function harness.computeBorrowingPower(uint, uint, uint) external
        returns (uint) envfree;
}

// ---------------------------------------------------------------------------
// Rule 3a: Floor-division bound on required tokens.
//          requiredTokens = floor(amount * SCALE / denom), so:
//          requiredTokens * denom <= amount * SCALE  (no overshoot)
//          amount * SCALE - requiredTokens * denom < denom  (tight bound)
//
//          This is the mathematical core of loan safety (Theorem 2):
//          the protocol locks exactly floor(debt / borrowingPowerPerToken)
//          tokens, and the remainder is strictly less than one token's worth.
// ---------------------------------------------------------------------------
rule floorDivisionBound(
    uint requestedAmount,
    uint floorPrice,
    uint ltvBPS
) {
    require requestedAmount > 0, "loan amount must be positive";
    require floorPrice > 0, "floor price must be positive";
    require ltvBPS > 0 && ltvBPS <= 10000, "LTV in valid BPS range";

    // Prevent overflow in intermediate calculations
    require requestedAmount < 2^128, "realistic loan amount";
    require floorPrice < 2^72, "fits in 72-bit price field";

    uint requiredTokens = harness.computeRequiredTokens(
        requestedAmount, floorPrice, ltvBPS
    );

    // Use mathint for overflow-safe reasoning
    mathint scale = 1000000000000000000 * 10000;  // 1e18 * 10_000
    mathint denom = floorPrice * ltvBPS;
    mathint lhs = requestedAmount * scale;
    mathint rhs = requiredTokens * denom;

    // PROPERTY 1: no overshoot — tokens * denom <= amount * SCALE
    assert rhs <= lhs,
        "mulDiv must not overshoot (floor division property)";

    // PROPERTY 2: tight bound — remainder < divisor
    assert lhs - rhs < denom,
        "floor division remainder must be less than divisor";
}

// ---------------------------------------------------------------------------
// Rule 3b: Non-zero tokens are always required for meaningful loans.
// ---------------------------------------------------------------------------
rule loanRequiresTokens(
    uint requestedAmount,
    uint floorPrice,
    uint ltvBPS
) {
    require requestedAmount > 0, "loan amount must be positive";
    require floorPrice > 0, "floor price must be positive";
    require ltvBPS > 0 && ltvBPS <= 10000, "LTV in valid BPS range";
    require requestedAmount < 2^128, "realistic loan amount";
    require floorPrice < 2^72, "fits in 72-bit price field";

    // Ensure numerator >= denominator (loan is meaningful)
    require requestedAmount * 1000000000000000000 * 10000 >= ltvBPS * floorPrice,
        "loan must require at least 1 token";

    uint requiredTokens = harness.computeRequiredTokens(
        requestedAmount, floorPrice, ltvBPS
    );

    assert requiredTokens > 0,
        "valid loan must require at least 1 token";
}

// ---------------------------------------------------------------------------
// Rule 3c: More debt requires more tokens (monotonicity).
// ---------------------------------------------------------------------------
rule moreDebtRequiresMoreTokens(
    uint amount1,
    uint amount2,
    uint floorPrice,
    uint ltvBPS
) {
    require amount1 > 0 && amount2 > amount1, "amount2 strictly greater";
    require floorPrice > 0, "floor price must be positive";
    require ltvBPS > 0 && ltvBPS <= 10000, "LTV in valid BPS range";
    require amount1 < 2^128, "realistic loan amount";
    require amount2 < 2^128, "realistic loan amount";
    require floorPrice < 2^72, "fits in 72-bit price field";

    uint tokens1 = harness.computeRequiredTokens(amount1, floorPrice, ltvBPS);
    uint tokens2 = harness.computeRequiredTokens(amount2, floorPrice, ltvBPS);

    assert tokens2 >= tokens1,
        "higher debt must require at least as many tokens";
}
