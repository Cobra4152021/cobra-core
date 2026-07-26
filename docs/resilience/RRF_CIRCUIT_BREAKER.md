# RRF Circuit Breaker

Per provider/model. States: `closed` → `open` → `half_open` → `closed|open`.

Defaults: failure threshold 5 / 60s window, open 30s, half-open probe limit 1, success threshold 2 to close.

Only `circuit_breaker_relevant` failures count. Cancellation does not open the circuit.
Open circuit is never overridden by a health probe alone.
