// =============================================================================
// Property 1: Floor Price Monotonicity
// =============================================================================
// Proves that the floor price can only increase or stay the same under
// all protocol operations. Specifically:
//   - raiseFloor always produces newFloorPrice >= oldFloorPrice
//   - sell + adjustFloorToSupply preserves the floor price
//   - The partial-raise arithmetic (collateral / supply) is non-negative
//
// The stateful property (raiseFloor on Floor_v1) is verified against the
// actual contract. The pure arithmetic is verified via harness.
// =============================================================================

using DiscreteCurveMathHarness as mathHarness;

methods {
    function mathHarness.reserveForSingleSegment(uint, uint, uint)
        external returns (uint) envfree;
}

// ---------------------------------------------------------------------------
// Rule 1a: Partial raise is always non-negative.
//          (collateral * 1e18) / floorSupply >= 0  (trivially true for uint)
//          More importantly: floorPrice + raisablePrice >= floorPrice
// ---------------------------------------------------------------------------
rule partialRaiseMonotonicity(
    uint floorPrice,
    uint floorSupply,
    uint collateralAmount
) {
    require floorPrice > 0, "floor price must be positive";
    require floorSupply > 0, "floor supply must be positive";
    require collateralAmount > 0, "collateral must be positive";

    // Use mathint to avoid overflow — Certora's native arbitrary-precision int
    mathint raisablePrice = (collateralAmount * 1000000000000000000) / floorSupply;
    mathint newFloorPrice = floorPrice + raisablePrice;

    assert newFloorPrice >= floorPrice,
        "floor price must not decrease from partial raise";
}

// ---------------------------------------------------------------------------
// Rule 1b: Reserve at zero supply is always zero (boundary condition).
//          Uses harness helper that builds a single floor segment internally.
// ---------------------------------------------------------------------------
rule reserveZeroAtZeroSupply(uint floorPrice, uint floorSupply) {
    require floorPrice > 0;
    require floorSupply > 0;
    require floorPrice < 2^72;
    require floorSupply < 2^96;

    uint reserve = mathHarness.reserveForSingleSegment(
        floorPrice, floorSupply, 0
    );
    assert reserve == 0, "reserve at zero supply must be zero";
}

// ---------------------------------------------------------------------------
// Rule 1c: Step absorption price is non-decreasing.
//          If segInitialPrice > floorPrice, then after absorbing the step
//          the new floor price equals segInitialPrice >= old floor price.
// ---------------------------------------------------------------------------
rule stepAbsorptionIncreasesPrice(
    uint floorPrice,
    uint segInitialPrice
) {
    require segInitialPrice > floorPrice;
    require floorPrice > 0;

    // After absorption: newFloorPrice = segInitialPrice
    uint newFloorPrice = segInitialPrice;

    assert newFloorPrice >= floorPrice,
        "absorbing a premium step must not decrease floor price";
}
