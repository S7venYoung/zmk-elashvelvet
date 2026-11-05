# Left split subscription investigation and candidate fix

## Verified observations (2026-11-05)

- Left application readback matches all 370944 bytes of the regular left UF2 from Actions 41371459929. This readback covers the application; CURRENT.UF2 does not cover the full settings partition, so it cannot establish whether bonds/theme cache exist.
- Diagnostic build 41985035110 exposes left CDC logging. A single-reset capture reaches ZMK main, matrix configuration and display initialization without a captured fatal error.
- At approximately 6.7 seconds, BAS reports notifications enabled. Subsequent split relay notifications repeatedly report `Device is not subscribed to characteristic` and `err=-22` with MTU 23. BAS alone does not prove an encrypted link.
- Receiver diagnostics show regular right acknowledgements and zero left acknowledgements. Right typing remains operational after receiver replug. A USB transport query initially needed a post-open delay; that timeout was not evidence of receiver failure.
- Receiver replug did not restore left relay acknowledgements.

## Candidate change

The pinned ZMK central starts discovery/subscription immediately on connection, while encrypted CCCs require security level 2. Its security callback previously returned unless a selected-layout handle had already been discovered. This leaves no first-discovery continuation at that callback and is consistent with the observed one-sided failure; the logs do not yet prove this is the only cause.

The Nano build now patches central.c to request/reuse level-2 security before discovery. A successful security callback resumes discovery even when the layout handle is still zero. Existing position handles avoid duplicate discovery, foreign connections are ignored, and errors do not erase bonds. No settings reset, keymap, display or bootloader changes are included. The unpushed waiting-page change is intentionally excluded: restoring typing is the priority.

Host tests compile the actual patched callbacks with assertions and sanitizers. They cover pre-encryption gating, the first security-success continuation, security errors, low-security callbacks, existing subscriptions, in-progress/error security requests and unrelated connections. This is a candidate requiring an explicitly requested Nano build and physical test; it is not a claimed hardware fix. The current left diagnostic UF2 can stay installed for logs while testing a candidate receiver.
