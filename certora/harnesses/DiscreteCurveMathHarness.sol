// SPDX-License-Identifier: LGPL-3.0-only
pragma solidity 0.8.28;

import {PackedSegment} from "@iss/types/PackedSegment_v1.sol";
import {PackedSegmentLib} from "@iss/libraries/PackedSegmentLib.sol";
import {
    DiscreteCurveMathLib_v1
} from "@iss/formulas/DiscreteCurveMathLib_v1.sol";
import {Math} from "@oz/utils/math/Math.sol";
import {FixedPointMathLib} from "@iss/libraries/FixedPointMathLib.sol";

/// @title  Certora harness for DiscreteCurveMathLib_v1
/// @notice Exposes library functions as external calls for CVL verification.
contract DiscreteCurveMathHarness {
    using PackedSegmentLib for PackedSegment;

    function calculateReserveForSupply(
        PackedSegment[] memory segments,
        uint targetSupply
    ) external pure returns (uint) {
        return DiscreteCurveMathLib_v1._calculateReserveForSupply(
            segments, targetSupply
        );
    }

    function calculatePurchaseReturn(
        PackedSegment[] memory segments,
        uint collateralToSpend,
        uint currentSupply
    ) external pure returns (uint tokensToMint, uint collateralSpent) {
        return DiscreteCurveMathLib_v1._calculatePurchaseReturn(
            segments, collateralToSpend, currentSupply
        );
    }

    function calculateSaleReturn(
        PackedSegment[] memory segments,
        uint tokensToSell,
        uint currentSupply
    ) external pure returns (uint collateralReturned, uint tokensBurned) {
        return DiscreteCurveMathLib_v1._calculateSaleReturn(
            segments, tokensToSell, currentSupply
        );
    }

    function validateSegmentArray(PackedSegment[] memory segments)
        external
        pure
    {
        DiscreteCurveMathLib_v1._validateSegmentArray(segments);
    }

    function createSegment(
        uint initialPrice,
        uint priceIncrease,
        uint supplyPerStep,
        uint numberOfSteps
    ) external pure returns (PackedSegment) {
        return DiscreteCurveMathLib_v1._createSegment(
            initialPrice, priceIncrease, supplyPerStep, numberOfSteps
        );
    }

    /// @notice Reserve for a single floor segment at a given supply.
    ///         Builds the 1-element array internally so CVL doesn't need to.
    function reserveForSingleSegment(
        uint initialPrice,
        uint supplyPerStep,
        uint targetSupply
    ) external pure returns (uint) {
        PackedSegment[] memory segs = new PackedSegment[](1);
        segs[0] = DiscreteCurveMathLib_v1._createSegment(
            initialPrice, 0, supplyPerStep, 1
        );
        return DiscreteCurveMathLib_v1._calculateReserveForSupply(
            segs, targetSupply
        );
    }

    /// @notice Reserve for a two-segment curve at a given supply.
    function reserveForTwoSegments(
        uint floorPrice, uint floorSupplyPerStep,
        uint seg1Price, uint seg1Increase, uint seg1SupplyPerStep, uint seg1Steps,
        uint targetSupply
    ) external pure returns (uint) {
        PackedSegment[] memory segs = new PackedSegment[](2);
        segs[0] = DiscreteCurveMathLib_v1._createSegment(
            floorPrice, 0, floorSupplyPerStep, 1
        );
        segs[1] = DiscreteCurveMathLib_v1._createSegment(
            seg1Price, seg1Increase, seg1SupplyPerStep, seg1Steps
        );
        return DiscreteCurveMathLib_v1._calculateReserveForSupply(
            segs, targetSupply
        );
    }

    /// @notice Purchase return for a two-segment curve.
    function purchaseOnTwoSegments(
        uint floorPrice, uint floorSPS,
        uint seg1Price, uint seg1Increase, uint seg1SPS, uint seg1Steps,
        uint collateralToSpend, uint currentSupply
    ) external pure returns (uint tokensToMint, uint collateralSpent) {
        PackedSegment[] memory segs = new PackedSegment[](2);
        segs[0] = DiscreteCurveMathLib_v1._createSegment(
            floorPrice, 0, floorSPS, 1
        );
        segs[1] = DiscreteCurveMathLib_v1._createSegment(
            seg1Price, seg1Increase, seg1SPS, seg1Steps
        );
        return DiscreteCurveMathLib_v1._calculatePurchaseReturn(
            segs, collateralToSpend, currentSupply
        );
    }

    /// @notice Direct segment reserve (bypasses array/loop overhead).
    function segmentReserve(
        uint initialPrice,
        uint priceIncrease,
        uint supplyPerStep,
        uint supplyToProcess
    ) external pure returns (uint) {
        return DiscreteCurveMathLib_v1._calculateSegmentReserve(
            initialPrice, priceIncrease, supplyPerStep, supplyToProcess
        );
    }

    /// @notice Purchase return for a single flat-floor segment.
    function purchaseOnSingleSegment(
        uint floorPrice, uint floorSPS,
        uint collateralToSpend, uint currentSupply
    ) external pure returns (uint tokensToMint, uint collateralSpent) {
        PackedSegment[] memory segs = new PackedSegment[](1);
        segs[0] = DiscreteCurveMathLib_v1._createSegment(
            floorPrice, 0, floorSPS, 1
        );
        return DiscreteCurveMathLib_v1._calculatePurchaseReturn(
            segs, collateralToSpend, currentSupply
        );
    }

    /// @notice Sale return for a single flat-floor segment.
    function saleOnSingleSegment(
        uint floorPrice, uint floorSPS,
        uint tokensToSell, uint currentSupply
    ) external pure returns (uint collateralReturned, uint tokensBurned) {
        PackedSegment[] memory segs = new PackedSegment[](1);
        segs[0] = DiscreteCurveMathLib_v1._createSegment(
            floorPrice, 0, floorSPS, 1
        );
        return DiscreteCurveMathLib_v1._calculateSaleReturn(
            segs, tokensToSell, currentSupply
        );
    }

    /// @notice Reserve for a single flat-floor segment at a given supply.
    function reserveForSingleFloorSegment(
        uint floorPrice, uint floorSPS, uint targetSupply
    ) external pure returns (uint) {
        PackedSegment[] memory segs = new PackedSegment[](1);
        segs[0] = DiscreteCurveMathLib_v1._createSegment(
            floorPrice, 0, floorSPS, 1
        );
        return DiscreteCurveMathLib_v1._calculateReserveForSupply(
            segs, targetSupply
        );
    }

    /// @notice Direct single-step purchase — same mulDiv/mulDivUp arithmetic
    ///         as _calculatePurchaseReturn Phase 2, but without loops, segment
    ///         arrays, or PackedSegment packing/unpacking overhead.
    ///         Used for MidStep verification where the segment-routing control
    ///         flow creates prohibitive SMT complexity.
    function directSingleStepPurchase(
        uint price, uint supplyPerStep,
        uint collateralBudget, uint currentSupply
    ) external pure returns (uint tokensMinted, uint collateralSpent) {
        uint SCALING_FACTOR = 1e18;
        if (collateralBudget == 0) return (0, 0);
        if (currentSupply >= supplyPerStep) return (0, 0);

        uint remainingCapacity = supplyPerStep - currentSupply;
        uint remainingCost = FixedPointMathLib._mulDivUp(
            remainingCapacity, price, SCALING_FACTOR
        );

        if (collateralBudget >= remainingCost) {
            // Complete the step (same as Phase 2 completing current step)
            tokensMinted = remainingCapacity;
            collateralSpent = remainingCost;
        } else {
            // Partial fill (same as Phase 2 partial fill and early return)
            tokensMinted = Math.mulDiv(
                collateralBudget, SCALING_FACTOR, price
            );
            collateralSpent = tokensMinted > 0
                ? FixedPointMathLib._mulDivUp(
                    tokensMinted, price, SCALING_FACTOR
                )
                : 0;
        }
    }

    /// @notice Direct single-step sale return — computes R(currentSupply) -
    ///         R(currentSupply - tokensSold) using _calculateSegmentReserve
    ///         directly (no loops, no PackedSegment overhead).
    function directSingleStepSale(
        uint price, uint supplyPerStep,
        uint tokensToSell, uint currentSupply
    ) external pure returns (uint collateralReturned, uint tokensBurned) {
        if (tokensToSell == 0) return (0, 0);
        if (tokensToSell > currentSupply) return (0, 0);

        tokensBurned = tokensToSell;
        uint reserveAtCurrent = DiscreteCurveMathLib_v1._calculateSegmentReserve(
            price, 0, supplyPerStep, currentSupply
        );
        uint reserveAfterSale = DiscreteCurveMathLib_v1._calculateSegmentReserve(
            price, 0, supplyPerStep, currentSupply - tokensToSell
        );
        collateralReturned = reserveAtCurrent - reserveAfterSale;
    }

    /// @notice Returns mulDivUp(n, price, WAD) and mulDivUp(n+1, price, WAD).
    ///         Both within-step and cross-boundary sloped monotonicity reduce to
    ///         this: ceil(n*price/WAD) <= ceil((n+1)*price/WAD).
    ///         Bypasses _calculateSegmentReserve entirely to avoid nonlinear
    ///         arithmetic series and modulo operations that cause SMT timeouts.
    function mulDivUpPair(
        uint n, uint price
    ) external pure returns (uint low, uint high) {
        uint SCALING_FACTOR = 1e18;
        low = FixedPointMathLib._mulDivUp(n, price, SCALING_FACTOR);
        high = FixedPointMathLib._mulDivUp(n + 1, price, SCALING_FACTOR);
    }

    /// @notice Sale return for a two-segment curve.
    function saleOnTwoSegments(
        uint floorPrice, uint floorSPS,
        uint seg1Price, uint seg1Increase, uint seg1SPS, uint seg1Steps,
        uint tokensToSell, uint currentSupply
    ) external pure returns (uint collateralReturned, uint tokensBurned) {
        PackedSegment[] memory segs = new PackedSegment[](2);
        segs[0] = DiscreteCurveMathLib_v1._createSegment(
            floorPrice, 0, floorSPS, 1
        );
        segs[1] = DiscreteCurveMathLib_v1._createSegment(
            seg1Price, seg1Increase, seg1SPS, seg1Steps
        );
        return DiscreteCurveMathLib_v1._calculateSaleReturn(
            segs, tokensToSell, currentSupply
        );
    }
}
