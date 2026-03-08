// SPDX-License-Identifier: LGPL-3.0-only
pragma solidity 0.8.28;

import {Math} from "@oz/utils/math/Math.sol";

/// @title  Certora harness for repayment and loan arithmetic
/// @notice Isolates the pure math from CreditFacility_v1 for CVL verification.
///         No storage, no ERC20 — just the arithmetic.
contract RepaymentHarness {

    // ---------------------------------------------------------------
    // Repayment arithmetic (mirrors _processPartialRepayment)
    // ---------------------------------------------------------------

    /// @notice Compute partial repayment outputs.
    /// @return tokensToUnlock  Issuance tokens unlocked
    /// @return newDebt         Remaining debt after repayment
    /// @return newLocked       Remaining locked tokens after repayment
    function partialRepayment(
        uint lockedTokens,
        uint remainingDebt,
        uint repayAmount
    )
        external
        pure
        returns (uint tokensToUnlock, uint newDebt, uint newLocked)
    {
        require(lockedTokens > 0 && remainingDebt > 0, "zero input");
        require(repayAmount > 0 && repayAmount < remainingDebt, "bad repay");

        tokensToUnlock = (lockedTokens * repayAmount) / remainingDebt;
        newDebt = remainingDebt - repayAmount;
        newLocked = lockedTokens - tokensToUnlock;
    }

    // ---------------------------------------------------------------
    // Borrow arithmetic (mirrors _borrow)
    // ---------------------------------------------------------------

    /// @notice Compute required issuance tokens for a loan.
    /// @return requiredTokens  Issuance tokens that must be locked
    function computeRequiredTokens(
        uint requestedAmount,
        uint floorPrice,
        uint ltvBPS
    ) external pure returns (uint requiredTokens) {
        require(requestedAmount > 0, "zero amount");
        require(floorPrice > 0, "zero price");
        require(ltvBPS > 0 && ltvBPS <= 10_000, "bad LTV");

        uint denom = ltvBPS * floorPrice;
        requiredTokens = Math.mulDiv(
            requestedAmount, 1e18 * 10_000, denom
        );
    }

    /// @notice Compute borrowing power of locked tokens.
    /// @return borrowingPower  Maximum debt these tokens can support
    function computeBorrowingPower(
        uint lockedTokens,
        uint floorPrice,
        uint ltvBPS
    ) external pure returns (uint borrowingPower) {
        require(lockedTokens > 0, "zero tokens");
        require(floorPrice > 0, "zero price");
        require(ltvBPS > 0 && ltvBPS <= 10_000, "bad LTV");

        borrowingPower = Math.mulDiv(
            lockedTokens * ltvBPS, floorPrice, 1e18 * 10_000
        );
    }
}
