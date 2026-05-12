import "./setup/setup.spec";

rule registerCreatesActiveListedNode(env e, uint256 amount) {
    setupFundedNode(e, amount);

    uint256 lengthBefore = getNodeAddressesLength();
    registerNode@withrevert(e, amount);
    assert !lastReverted, "funded registration reverted";

    assert getNodeAddressAt(lengthBefore) == e.msg.sender, "registered node not appended";
    assert getNodeAddressAt(lengthBefore) != 0, "registered zero node";
    assert getNodeActive(e.msg.sender), "registered node not active";
}

rule duplicateRegistrationReverts(env e, uint256 amount) {
    setupFundedNode(e, amount);

    registerNode@withrevert(e, amount);
    require !lastReverted;
    certoraSetTokenBalanceAndAllowance(e, e.msg.sender, amount);
    registerNode@withrevert(e, amount);

    assert lastReverted, "duplicate registration succeeded";
}

definition listedInBoundedPrefix(address node) returns bool =
    (getNodeAddressesLength() > 0 && getNodeAddressAt(0) == node)
    || (getNodeAddressesLength() > 1 && getNodeAddressAt(1) == node)
    || (getNodeAddressesLength() > 2 && getNodeAddressAt(2) == node);

definition boundedListedEntriesActiveAndNonzero() returns bool =
    (getNodeAddressesLength() <= 0 || (getNodeAddressAt(0) != 0 && getNodeActive(getNodeAddressAt(0))))
    && (getNodeAddressesLength() <= 1 || (getNodeAddressAt(1) != 0 && getNodeActive(getNodeAddressAt(1))))
    && (getNodeAddressesLength() <= 2 || (getNodeAddressAt(2) != 0 && getNodeActive(getNodeAddressAt(2))));

definition boundedListedEntriesUnique() returns bool =
    (getNodeAddressesLength() <= 1 || getNodeAddressAt(0) != getNodeAddressAt(1))
    && (getNodeAddressesLength() <= 2 || getNodeAddressAt(0) != getNodeAddressAt(2))
    && (getNodeAddressesLength() <= 2 || getNodeAddressAt(1) != getNodeAddressAt(2));

definition boundedActiveNodeRepresented(address node) returns bool =
    getNodeAddressesLength() > LOOP_ITER_CVL()
    || !getNodeActive(node)
    || listedInBoundedPrefix(node);

rule successfulCallsPreserveBoundedNodeAddressShape(env e, method f, calldataarg args, address trackedNode)
    filtered { f -> stakingStateChangingFunction(f) }
{
    setup(e);
    require getNodeAddressesLength() <= LOOP_ITER_CVL();
    require boundedListedEntriesActiveAndNonzero();
    require boundedListedEntriesUnique();
    require boundedActiveNodeRepresented(e.msg.sender);
    require boundedActiveNodeRepresented(trackedNode);

    f@withrevert(e, args);

    assert lastReverted
        || getNodeAddressesLength() > LOOP_ITER_CVL()
        || (
            boundedListedEntriesActiveAndNonzero()
            && boundedListedEntriesUnique()
            && boundedActiveNodeRepresented(e.msg.sender)
            && boundedActiveNodeRepresented(trackedNode)
        ),
        "successful call broke bounded node-address shape";
}

invariant bucketReportersAndPricesStayAligned(uint256 bucketNumber)
    getBucketReportersLength(bucketNumber) == getBucketPricesLength(bucketNumber)
filtered { f -> !isHarnessHelper(f) }
{ preserved with (env e) { setup(e); } }
