import "./methods.spec";

definition LOOP_ITER_CVL() returns mathint = 3;
definition MAX_REASONABLE_PRICE() returns mathint = 1000000000000000000000000000000;

definition isHarnessHelper(method f) returns bool =
    f.selector == sig:certoraSetOracleToken(address).selector
    || f.selector == sig:certoraSetTokenBalance(address,uint256).selector
	    || f.selector == sig:certoraSetTokenBalanceAndAllowance(address,uint256).selector
	    || f.selector == sig:certoraPrepareStake(address,uint256).selector
	    || f.selector == sig:certoraSeedSlashScenario(address,uint256,uint256,uint256,uint256).selector
	    || f.selector == sig:certoraSeedBucketReport(address,uint256,uint256,uint256,bool).selector
	    || f.selector == sig:certoraSeedBucketReports3(uint256,uint256,address,uint256,bool,address,uint256,bool,address,uint256,bool).selector
	    || f.selector == sig:certoraSeedUnrecordedBucketReports3(uint256,address,uint256,address,uint256,address,uint256).selector
	    || f.selector == sig:certoraSeedNode(address,uint256,uint256,uint256,uint256,uint256,bool).selector;

definition stakingStateChangingFunction(method f) returns bool =
    f.contract == currentContract
    && !f.isView
    && !f.isPure
    && !isHarnessHelper(f);

function setup(env e) {
    require e.msg.sender != 0;
    require e.msg.sender != currentContract;
}

function setupValidState(env e) {
    setup(e);
    require getNodeAddressesLength() <= LOOP_ITER_CVL();
}

function setupFundedNode(env e, uint256 amount) {
    setup(e);
    require amount >= MINIMUM_STAKE();
    require amount < MAX_REASONABLE_PRICE();
    require !getNodeActive(e.msg.sender);
    require getNodeAddressesLength() < LOOP_ITER_CVL();
    certoraPrepareStake(e, e.msg.sender, amount);
}
