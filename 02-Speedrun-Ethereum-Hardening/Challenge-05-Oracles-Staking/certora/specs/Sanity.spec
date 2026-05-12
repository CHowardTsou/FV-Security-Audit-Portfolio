import "./setup/setup.spec";

rule canRegisterFundedNode(env e, uint256 amount) {
    setupFundedNode(e, amount);

    registerNode@withrevert(e, amount);

    satisfy !lastReverted;
}

rule canReportAfterRegistering(env e, uint256 amount, uint256 price) {
    setupFundedNode(e, amount);
    require price > 0;
    require price < MAX_REASONABLE_PRICE();

    registerNode@withrevert(e, amount);
    require !lastReverted;

    reportPrice@withrevert(e, price);

    satisfy !lastReverted;
}

rule canClaimRewardAfterReport(env e, uint256 amount, uint256 price) {
    setupFundedNode(e, amount);
    require price > 0;
    require price < MAX_REASONABLE_PRICE();

    registerNode@withrevert(e, amount);
    require !lastReverted;
    reportPrice@withrevert(e, price);
    require !lastReverted;

    claimReward@withrevert(e);

    satisfy !lastReverted;
}
