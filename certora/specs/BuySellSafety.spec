// =============================================================================
// Property 6: Buy/Sell Safety
// =============================================================================
// Proves that buy and sell operations on the bonding curve preserve the
// reserve invariant:
//   - Purchase: collateral spent never exceeds budget (no overspend)
//   - Purchase: minting tokens requires spending collateral (no free tokens)
//   - Sale: collateral returned does not exceed the reserve at current supply
//   - Sale: tokens burned does not exceed tokens offered for sale
//   - Round-trip: buy-then-sell does not create collateral (no arbitrage)
//
// Strategy:
//   Fresh rules (currentSupply=0) use purchaseOnSingleSegment which calls
//   the actual _calculatePurchaseReturn implementation.
//
//   MidStep rules (currentSupply>0) use directSingleStepPurchase/Sale which
//   implement the same mulDiv/mulDivUp arithmetic as _calculatePurchaseReturn
//   Phase 2 and _calculateSaleReturn, but without the segment-routing loop
//   and PackedSegment packing/unpacking that create prohibitive SMT
//   complexity. The direct functions use the same FixedPointMathLib._mulDivUp
//   and Math.mulDiv calls as the real implementation.
//
//   Rules 6c/6d use the two-segment harness since they already verify quickly.
// =============================================================================

using DiscreteCurveMathHarness as harness;

methods {
    function harness.purchaseOnTwoSegments(uint, uint, uint, uint, uint, uint, uint, uint)
        external returns (uint, uint) envfree;
    function harness.saleOnTwoSegments(uint, uint, uint, uint, uint, uint, uint, uint)
        external returns (uint, uint) envfree;
    function harness.reserveForTwoSegments(uint, uint, uint, uint, uint, uint, uint)
        external returns (uint) envfree;
    function harness.purchaseOnSingleSegment(uint, uint, uint, uint)
        external returns (uint, uint) envfree;
    function harness.saleOnSingleSegment(uint, uint, uint, uint)
        external returns (uint, uint) envfree;
    function harness.directSingleStepPurchase(uint, uint, uint, uint)
        external returns (uint, uint) envfree;
    function harness.directSingleStepSale(uint, uint, uint, uint)
        external returns (uint, uint) envfree;
    function harness.segmentReserve(uint, uint, uint, uint)
        external returns (uint) envfree;
}

// ---------------------------------------------------------------------------
// Rule 6a: No overspend — fresh start (currentSupply == 0).
//          Verified through the actual _calculatePurchaseReturn path.
// ---------------------------------------------------------------------------
rule noOverspendFresh(
    uint floorPrice, uint floorSPS, uint collateralToSpend
) {
    require floorPrice > 0 && floorPrice < 2^72, "valid floor price";
    require floorSPS > 0 && floorSPS < 2^96, "valid floor supply per step";
    require collateralToSpend > 0, "must spend something";

    uint tokensToMint; uint collateralSpent;
    tokensToMint, collateralSpent = harness.purchaseOnSingleSegment(
        floorPrice, floorSPS, collateralToSpend, 0
    );

    assert collateralSpent <= collateralToSpend,
        "cannot spend more collateral than budget (fresh)";
}

// ---------------------------------------------------------------------------
// Rule 6a': No overspend — mid-step (0 < currentSupply < capacity).
//           Uses direct single-step purchase (same arithmetic, no loop).
// ---------------------------------------------------------------------------
rule noOverspendMidStep(
    uint floorPrice, uint floorSPS,
    uint collateralToSpend, uint currentSupply
) {
    require floorPrice > 0 && floorPrice < 2^72, "valid floor price";
    require floorSPS > 0 && floorSPS < 2^96, "valid floor supply per step";
    require collateralToSpend > 0, "must spend something";
    require currentSupply > 0 && currentSupply < floorSPS,
        "mid-step: within single step capacity";

    uint tokensToMint; uint collateralSpent;
    tokensToMint, collateralSpent = harness.directSingleStepPurchase(
        floorPrice, floorSPS, collateralToSpend, currentSupply
    );

    assert collateralSpent <= collateralToSpend,
        "cannot spend more collateral than budget (mid-step)";
}

// ---------------------------------------------------------------------------
// Rule 6b: No free tokens — fresh start.
// ---------------------------------------------------------------------------
rule noFreeTokensFresh(
    uint floorPrice, uint floorSPS, uint collateralToSpend
) {
    require floorPrice > 0 && floorPrice < 2^72, "valid floor price";
    require floorSPS > 0 && floorSPS < 2^96, "valid floor supply per step";
    require collateralToSpend > 0, "must spend something";

    uint tokensToMint; uint collateralSpent;
    tokensToMint, collateralSpent = harness.purchaseOnSingleSegment(
        floorPrice, floorSPS, collateralToSpend, 0
    );

    assert tokensToMint > 0 => collateralSpent > 0,
        "minted tokens must cost collateral (fresh)";
}

// ---------------------------------------------------------------------------
// Rule 6b': No free tokens — mid-step.
// ---------------------------------------------------------------------------
rule noFreeTokensMidStep(
    uint floorPrice, uint floorSPS,
    uint collateralToSpend, uint currentSupply
) {
    require floorPrice > 0 && floorPrice < 2^72, "valid floor price";
    require floorSPS > 0 && floorSPS < 2^96, "valid floor supply per step";
    require collateralToSpend > 0, "must spend something";
    require currentSupply > 0 && currentSupply < floorSPS,
        "mid-step: within single step capacity";

    uint tokensToMint; uint collateralSpent;
    tokensToMint, collateralSpent = harness.directSingleStepPurchase(
        floorPrice, floorSPS, collateralToSpend, currentSupply
    );

    assert tokensToMint > 0 => collateralSpent > 0,
        "minted tokens must cost collateral (mid-step)";
}

// ---------------------------------------------------------------------------
// Rule 6c: Sale never returns more collateral than the reserve holds.
//          (Already verified with two-segment harness.)
// ---------------------------------------------------------------------------
rule saleDoesNotDrainReserve(
    uint floorPrice, uint floorSPS,
    uint seg1Price, uint seg1Increase, uint seg1SPS, uint seg1Steps,
    uint tokensToSell, uint currentSupply
) {
    require floorPrice > 0 && floorPrice < 2^72, "valid floor price";
    require floorSPS > 0 && floorSPS < 2^96, "valid floor supply per step";
    require seg1Price > 0 && seg1Price < 2^72, "valid segment price";
    require seg1Increase > 0 && seg1Increase < 2^72, "valid price increase";
    require seg1SPS > 0 && seg1SPS < 2^96, "valid segment supply per step";
    require seg1Steps > 1 && seg1Steps < 2^16, "valid step count";
    require tokensToSell > 0, "must sell something";
    require currentSupply > 0, "must have supply to sell";
    require tokensToSell <= currentSupply, "cannot sell more than supply";

    uint reserveBefore = harness.reserveForTwoSegments(
        floorPrice, floorSPS, seg1Price, seg1Increase, seg1SPS, seg1Steps,
        currentSupply
    );

    uint collateralReturned; uint tokensBurned;
    collateralReturned, tokensBurned = harness.saleOnTwoSegments(
        floorPrice, floorSPS, seg1Price, seg1Increase, seg1SPS, seg1Steps,
        tokensToSell, currentSupply
    );

    assert collateralReturned <= reserveBefore,
        "sale cannot return more collateral than reserve holds";
}

// ---------------------------------------------------------------------------
// Rule 6d: Tokens burned never exceed tokens offered for sale.
//          (Already verified with two-segment harness.)
// ---------------------------------------------------------------------------
rule burnDoesNotExceedSale(
    uint floorPrice, uint floorSPS,
    uint seg1Price, uint seg1Increase, uint seg1SPS, uint seg1Steps,
    uint tokensToSell, uint currentSupply
) {
    require floorPrice > 0 && floorPrice < 2^72, "valid floor price";
    require floorSPS > 0 && floorSPS < 2^96, "valid floor supply per step";
    require seg1Price > 0 && seg1Price < 2^72, "valid segment price";
    require seg1Increase > 0 && seg1Increase < 2^72, "valid price increase";
    require seg1SPS > 0 && seg1SPS < 2^96, "valid segment supply per step";
    require seg1Steps > 1 && seg1Steps < 2^16, "valid step count";
    require tokensToSell > 0, "must sell something";
    require currentSupply > 0, "must have supply";
    require tokensToSell <= currentSupply, "cannot sell more than supply";

    uint collateralReturned; uint tokensBurned;
    collateralReturned, tokensBurned = harness.saleOnTwoSegments(
        floorPrice, floorSPS, seg1Price, seg1Increase, seg1SPS, seg1Steps,
        tokensToSell, currentSupply
    );

    assert tokensBurned <= tokensToSell,
        "cannot burn more tokens than offered for sale";
}

// ---------------------------------------------------------------------------
// Rule 6e: No round-trip profit — fresh start.
//          Verified through the actual _calculatePurchaseReturn/SaleReturn.
// ---------------------------------------------------------------------------
rule noRoundTripProfitFresh(
    uint floorPrice, uint floorSPS, uint collateralToSpend
) {
    require floorPrice > 0 && floorPrice < 2^72, "valid floor price";
    require floorSPS > 0 && floorSPS < 2^96, "valid floor supply per step";
    require collateralToSpend > 0, "must spend something";

    // Step 1: Buy at supply 0
    uint tokensToMint; uint collateralSpent;
    tokensToMint, collateralSpent = harness.purchaseOnSingleSegment(
        floorPrice, floorSPS, collateralToSpend, 0
    );

    require tokensToMint > 0, "must mint tokens for round-trip test";

    // Step 2: Sell back at new supply = tokensToMint
    uint collateralReturned; uint tokensBurned;
    collateralReturned, tokensBurned = harness.saleOnSingleSegment(
        floorPrice, floorSPS, tokensToMint, tokensToMint
    );

    assert collateralReturned <= collateralSpent,
        "round-trip must not produce profit (fresh)";
}

// ---------------------------------------------------------------------------
// Rule 6e': No round-trip profit — mid-step.
//           Uses direct single-step purchase and sale (same arithmetic).
// ---------------------------------------------------------------------------
rule noRoundTripProfitMidStep(
    uint floorPrice, uint floorSPS,
    uint collateralToSpend, uint currentSupply
) {
    require floorPrice > 0 && floorPrice < 2^72, "valid floor price";
    require floorSPS > 0 && floorSPS < 2^96, "valid floor supply per step";
    require collateralToSpend > 0, "must spend something";
    require currentSupply > 0 && currentSupply < floorSPS,
        "mid-step: within single step capacity";

    // Step 1: Buy
    uint tokensToMint; uint collateralSpent;
    tokensToMint, collateralSpent = harness.directSingleStepPurchase(
        floorPrice, floorSPS, collateralToSpend, currentSupply
    );

    require tokensToMint > 0, "must mint tokens for round-trip test";

    // Step 2: Sell back
    mathint newSupplyMath = currentSupply + tokensToMint;
    require newSupplyMath <= floorSPS, "new supply within step capacity";
    uint newSupply = require_uint256(newSupplyMath);

    uint collateralReturned; uint tokensBurned;
    collateralReturned, tokensBurned = harness.directSingleStepSale(
        floorPrice, floorSPS, tokensToMint, newSupply
    );

    assert collateralReturned <= collateralSpent,
        "round-trip must not produce profit (mid-step)";
}
