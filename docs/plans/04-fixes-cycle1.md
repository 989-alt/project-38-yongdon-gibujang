# Fixes — Cycle 1

1. Added `[hidden]{display:none!important}` to the global CSS reset so the `hidden` attribute reliably wins over component classes (`.empty-chart`, `.empty-state`, `.summary-line`).
   - Rationale: UA default for `[hidden]` is `display:none` with element-level specificity, which loses to any class rule that sets `display`. The explicit `!important` rule guarantees correctness without us needing to remember to override every component class.
