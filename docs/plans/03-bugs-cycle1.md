# Bugs — Cycle 1

## Found
1. **P1 · CSS specificity bug** — `.empty-chart{display:grid}` overrides UA `[hidden]{display:none}`. Empty-state divs (`#bar-empty`, `#donut-empty`, `#empty-state`, `#donut-summary`) remain visible even when `hidden` attribute is set, causing the chart cards to show both the chart and "아직 지출 기록이 없어요" text simultaneously.
   - **Repro**: Add any expense → bar chart card shows chart AND empty message under it.
   - **Fix**: Global `[hidden]{display:none!important}` rule.

## Not bugs (false alarms)
- e2e test reports PASS, including canvas pixels check — only the visible empty-text overlap was a regression caught from the screenshot.
