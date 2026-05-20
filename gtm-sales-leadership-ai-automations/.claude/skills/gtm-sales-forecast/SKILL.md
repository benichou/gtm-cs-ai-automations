---
name: gtm-sales-forecast
description: Roll up the open sales pipeline by forecast category (Commit / Best Case / Pipeline / Omitted) for a sales leader. Trigger when the user asks "what's my forecast", "how will we land this period", "what's my commit", "show me the forecast roll-up", "forecast by category", or asks for the prob-weighted forecast number. Optionally scoped to a close-date window or a single owner.
---

# gtm-sales-forecast skill

Answer "will I hit my number this period?" by calling the `roll_up_forecast` tool on the `gtm-sales-leadership` Model Context Protocol server and summarizing the result for a Sales VP.

## When to use

Trigger phrases include:
- "What's my forecast?"
- "What's my Commit / Best Case for this period?"
- "How will we land this quarter / this month?"
- "Show me the forecast roll-up"
- "Forecast by category"
- "What's my weighted pipeline?"

Do NOT use this skill for per-deal inspection (use `gtm-sales-at-risk`) or per-rep performance (use `gtm-sales-rep-scorecard`).

## Steps

1. **Parse the user's intent.** If they named a date or month (e.g. "this month", "end of May", "by 2026-05-31"), extract it as the `period_end` argument in ISO `YYYY-MM-DD` format. If they named a rep (e.g. "for J. Torres"), pass that as `owner`. Otherwise both are None.

2. **Call** `roll_up_forecast(period_end=..., owner=...)` on the `gtm-sales-leadership` Model Context Protocol server.

3. **Format the response** exactly like this:

   ```
   ## Pipeline forecast — as of <as_of>
   <If filters set, add a one-line filter summary, e.g. "Filter: closing by 2026-05-31">

   - **Commit**: $<commit_arr> · <Commit count> deals
   - **Best Case**: $<best_case_arr> · <Best Case count> deals
   - **Pipeline**: $<pipeline_arr> · <Pipeline count> deals
   - **Omitted**: $<omitted_arr> · <Omitted count> deals (rep-excluded)

   **Total open**: $<total_arr> across <total_deals> deals
   **Prob-weighted**: $<total_weighted_arr>
   **Commit + Best Case**: $<commit_plus_best_case_arr>
   ```

   Format dollar amounts with commas (e.g. `$1,269,000`). Round weighted ARR to the nearest dollar.

4. **End with one tactical observation** grounded in the numbers — e.g. "Weighted is well below Commit + Best Case; some of those deals look optimistic." or "Commit is light vs. Best Case — leaning on Best Case to hit the number means execution risk." Don't invent — just observe what the data shows.

## Failure handling

- If the Model Context Protocol server isn't registered, the tool won't be callable. Tell the user to add `gtm-sales-leadership` to `.claude/settings.json` (see the plugin README) and restart.
- If the tool raises an error, surface it verbatim. Never fabricate forecast numbers.
