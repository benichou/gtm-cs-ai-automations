---
name: gtm-sales-at-risk
description: Surface the top-N open deals most at risk of slipping, with a scored reason breakdown, for a sales leader. Trigger when the user asks "which deals are at risk", "what should I inspect this week", "show me deals at risk of slipping", "which deals need exec attention", "give me the inspection list", "where could the forecast slip", or "deals that need attention".
---

# gtm-sales-at-risk skill

Surface the deals a Sales VP should personally inspect this week. Calls the `rank_deals_by_risk` tool on the `gtm-sales-leadership` Model Context Protocol server, which scores each deal on five transparent factors (max score 10):

- **+3** stale (no activity > 14 days)
- **+3** overdue (close_date already in the past)
- **+2** blank next_step on a late-stage deal
- **+1** single-threaded (only 1 contact) on a late-stage deal
- **+1** in forecast (Commit or Best Case — slippage hurts the number directly)

## When to use

Trigger phrases include:
- "Which deals are at risk?"
- "What should I inspect this week?"
- "Show me deals at risk of slipping"
- "Which deals need exec attention?"
- "Give me the inspection list"
- "Where could the forecast slip?"
- "What needs my attention?"

Do NOT use for forecast totals (use `gtm-sales-forecast`) or rep-level patterns (use `gtm-sales-rep-scorecard`).

## Steps

1. **Determine top_n.** Default to 5 for an exec briefing; if the user says "top 10" or "all of them", honor it (cap at 20).

2. **Call** `rank_deals_by_risk(top_n=...)`.

3. **Format the response** exactly like this:

   ```
   ## Top <N> deals to inspect — as of <as_of>
   <scored_deals_total> deals scored, top <N> = $<top_n_arr> ($<top_n_weighted_arr> weighted)

   <For each deal:>
   ### <rank>. <opportunity_id> · <account_name> — <stage> · $<arr> · <owner_name>
   **Risk score: <risk_score>/10**
   <For each factor in risk_factors:>
   - <factor>
   <If next_step is not null:>
   _Next step:_ <next_step>
   ```

   Format ARR with commas.

4. **End with one tactical recommendation** — e.g. "Three of the top 5 are J. Torres deals. Worth a 1:1 Monday rather than scattering follow-ups." or "Two deals are both stale AND in forecast — surface these to the owner first." Don't fabricate.

## Failure handling

- If `top_n` is out of range, default to 5.
- If the tool raises, surface verbatim. Never invent risk reasons.
