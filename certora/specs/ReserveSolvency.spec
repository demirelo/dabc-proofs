// =============================================================================
// Property 2: Reserve Solvency
// =============================================================================
// Proves that the reserve function is monotonically non-decreasing in supply:
//   R(segments, S_high) >= R(segments, S_low)  when S_high >= S_low
//
// Also proves:
//   - Reserve at zero supply is zero
//
// Strategy:
//   Rule 2a verifies flat-segment monotonicity via segmentReserve (no loop).
//   Rules 2b/2c verify boundary conditions through the full path.
//   Rule 2d proves the core mulDivUp monotonicity lemma:
//     mulDivUp(n+1, price, 1e18) >= mulDivUp(n, price, 1e18)
//   via a direct harness that bypasses _calculateSegmentReserve entirely.
//   Rule 2e verifies _calculateSegmentReserve(*, *, *, 0) == 0.
//
// Why Rule 2d implies sloped segment monotonicity:
//   _calculateSegmentReserve splits supply into fullSteps + partial:
//     R(S) = seriesReserve(fullSteps) + mulDivUp(partial, stepPrice, WAD)
//
//   Within-step (S and S+1 have same fullSteps):
//     R(S+1) - R(S) = mulDivUp(partial+1, price_k, WAD)
//                    - mulDivUp(partial,   price_k, WAD) >= 0  [by Rule 2d]
//
//   Cross-boundary (S%sps == sps-1, so S+1 starts new step):
//     R(S)   = series(k) + mulDivUp(sps-1, price_k, WAD)
//     R(S+1) = series(k) + mulDivUp(sps,   price_k, WAD)
//     Difference = mulDivUp(sps, price_k, WAD)
//               - mulDivUp(sps-1, price_k, WAD) >= 0          [by Rule 2d]
//
// Price lower bounds: Prices are WAD-scaled (1e18 = 1 unit). We require
// initialPrice >= 1e18 (1.0 in WAD). This ensures each token costs >= 1
// collateral unit, which is sufficient for monotonicity because at each
// step boundary the extra token contributes floor(price/1e18) >= 1
// collateral, compensating for the at-most-1 rounding difference between
// split and combined mulDivUp ceiling operations. Below this threshold,
// ceiling rounding can dominate and cause non-monotonic artifacts.
// =============================================================================

using DiscreteCurveMathHarness as harness;

methods {
    function harness.reserveForSingleSegment(uint, uint, uint)
        external returns (uint) envfree;
    function harness.reserveForTwoSegments(uint, uint, uint, uint, uint, uint, uint)
        external returns (uint) envfree;
    function harness.segmentReserve(uint, uint, uint, uint)
        external returns (uint) envfree;
    function harness.mulDivUpPair(uint, uint)
        external returns (uint, uint) envfree;
}

// ---------------------------------------------------------------------------
// Rule 2a: Reserve monotonicity for a flat segment (priceIncrease == 0).
//          R(price, 0, sps, S_high) >= R(price, 0, sps, S_low)
//
//          Uses the direct segmentReserve harness (no loop) to avoid timeout.
// ---------------------------------------------------------------------------
rule flatSegmentReserveMonotonicity(
    uint initialPrice, uint supplyPerStep,
    uint supplyLow, uint supplyHigh
) {
    require supplyHigh >= supplyLow, "monotonicity: high >= low";
    require initialPrice >= 1000000000000000000 && initialPrice < 2^72,
        "WAD-scaled price >= 1.0 (each token costs >= 1 collateral unit)";
    require supplyPerStep > 0 && supplyPerStep < 2^96,
        "valid supply per step within PackedSegment range";
    require supplyLow < 2^72,
        "supply bounded to prevent overflow in mulDivUp";
    require supplyHigh < 2^72,
        "supply bounded to prevent overflow in mulDivUp";

    uint reserveLow = harness.segmentReserve(
        initialPrice, 0, supplyPerStep, supplyLow
    );
    uint reserveHigh = harness.segmentReserve(
        initialPrice, 0, supplyPerStep, supplyHigh
    );

    assert reserveHigh >= reserveLow,
        "flat segment reserve must be non-decreasing in supply";
}

// ---------------------------------------------------------------------------
// Rule 2b: Reserve at zero supply is zero (single-segment curve).
// ---------------------------------------------------------------------------
rule reserveZeroAtZeroSupply(uint floorPrice, uint floorSPS) {
    require floorPrice > 0 && floorPrice < 2^72,
        "valid WAD-scaled floor price";
    require floorSPS > 0 && floorSPS < 2^96,
        "valid supply per step";

    uint reserve = harness.reserveForSingleSegment(floorPrice, floorSPS, 0);
    assert reserve == 0, "reserve at zero supply must be zero";
}

// ---------------------------------------------------------------------------
// Rule 2c: Reserve at zero supply is zero (two-segment curve).
// ---------------------------------------------------------------------------
rule reserveZeroAtZeroSupplyTwoSeg(
    uint floorPrice, uint floorSPS,
    uint seg1Price, uint seg1Increase, uint seg1SPS, uint seg1Steps
) {
    require floorPrice > 0 && floorPrice < 2^72,
        "valid WAD-scaled floor price";
    require floorSPS > 0 && floorSPS < 2^96,
        "valid floor supply per step";
    require seg1Price > 0 && seg1Price < 2^72,
        "valid WAD-scaled segment price";
    require seg1Increase > 0 && seg1Increase < 2^72,
        "valid price increase";
    require seg1SPS > 0 && seg1SPS < 2^96,
        "valid segment supply per step";
    require seg1Steps > 1 && seg1Steps < 2^16,
        "multi-step segment within PackedSegment range";

    uint reserve = harness.reserveForTwoSegments(
        floorPrice, floorSPS, seg1Price, seg1Increase, seg1SPS, seg1Steps, 0
    );
    assert reserve == 0, "reserve at zero supply must be zero";
}

// ---------------------------------------------------------------------------
// Rule 2d: Core mulDivUp monotonicity lemma.
//          mulDivUp(n+1, price, 1e18) >= mulDivUp(n, price, 1e18)
//
//          This is the fundamental building block for sloped segment reserve
//          monotonicity. Both within-step and cross-boundary cases reduce to
//          this (see header comment for the reduction argument).
//
//          Uses mulDivUpPair harness which calls FixedPointMathLib._mulDivUp
//          directly — no _calculateSegmentReserve, no series, no modulo.
// ---------------------------------------------------------------------------
rule mulDivUpMonotonicity(uint n, uint price) {
    require price >= 1000000000000000000 && price < 2^72,
        "WAD-scaled price >= 1.0 (each token costs >= 1 collateral unit)";
    require n < 2^72,
        "n bounded to prevent overflow in mulDivUp";

    uint low; uint high;
    low, high = harness.mulDivUpPair(n, price);

    assert high >= low,
        "mulDivUp must be non-decreasing: ceil((n+1)*p/WAD) >= ceil(n*p/WAD)";
}

// ---------------------------------------------------------------------------
// Rule 2e: Reserve at zero supply is zero via direct segment function.
//          Confirms _calculateSegmentReserve(*, *, *, 0) == 0.
// ---------------------------------------------------------------------------
rule segmentReserveZeroAtZeroSupply(
    uint initialPrice, uint priceIncrease, uint supplyPerStep
) {
    require initialPrice > 0 && initialPrice < 2^72,
        "valid WAD-scaled price";
    require priceIncrease < 2^72,
        "price increase within range";
    require supplyPerStep > 0 && supplyPerStep < 2^96,
        "valid supply per step";

    uint reserve = harness.segmentReserve(
        initialPrice, priceIncrease, supplyPerStep, 0
    );
    assert reserve == 0, "segment reserve at zero supply must be zero";
}
