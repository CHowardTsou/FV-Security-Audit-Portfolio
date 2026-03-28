methods {
    function gateThree(bytes8) external returns (bool);
}

// ─────────────────────────────────────────────────────────────
// RULE 1: Certora finds the valid gatekey for a known sender
// This FAILS — giving you the concrete gatekey as counterexample
// ─────────────────────────────────────────────────────────────
rule gatethreereturn(env e) {
    bytes8 gatekey;
    require e.msg.sender == 0x980C2DB9dDbBda9E9C6621A5DF646C4ad03Bb368; // your address
    require e.msg.value == 0;

    gateThree@withrevert(e, gatekey);

    // Assert it always reverts — Certora FAILS this and shows
    // the exact gatekey value that passes all 3 conditions
    assert lastReverted;
}
