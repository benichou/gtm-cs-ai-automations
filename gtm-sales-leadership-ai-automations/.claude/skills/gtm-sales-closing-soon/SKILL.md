---
name: gtm-sales-closing-soon
description: List open deals closing on or before a given date for a sales leader. Trigger when the user asks "what's closing this month / this week / by end of quarter", "show me deals closing by <date>", "what deals are coming due", "this month's pipeline", or "what's landing in May / June / Q2".
---

# gtm-sales-closing-soon skill

Answer "what's actually going to close this period?" by calling the `list_deals_closing_by` tool on the `gtm-sales-leadership` Model Context Protocol server.

## When to use

Trigger phrases include:
- "What's closing this month / this week?"
- "Deals closing by end of May / Q2 / end of quarter"
- "What's coming due this period?"
- "Show me the close list"
- "What's landing in May?"

Do NOT use this skill for a generic forecast number (use `gtm-sales-forecast`) or for deal-level risk inspection (use `gtm-sales-at-risk`).

## Steps

1. **Extract the close-by date.** Convert whatever the user said to an ISO `YYYY-MM-DD` date. Examples:
   - "this month" → last day of the current month (anchor on `as_of` if needed)
   - "end of May" → `2026-05-31`
   - "by next Friday" → resolve relative to today
   - If the user gives no date and the request is ambiguous, ask one clarifying question.

2. **Call** `list_deals_closing_by(period_end="<ISO date>")`.

3. **Format the response** exactly like this:

   ```
   ## Deals closing by <period_end> — <deal_count> deals · $<total_arr> · $<total_weighted_arr> weighted

   <For each deal, sorted by close_date ascending:>
   - **<opportunity_id>** · <account_name> · <stage> · $<arr> · close <close_date> · <forecast_category> · <owner_name>
     <If days_since_activity > 14:> ⚠️ stale: <days_since_activity>d no activity
     <If next_step is null and stage is Proposal or Negotiation:> ⚠️ blank next_step
   ```

   Format ARR with commas. Limit to the top 15 deals; if there are more, append a note `(+N more deals not shown)`.

4. **End with one observation** — e.g. "5 of these 11 deals have no logged next_step — worth a Monday inspection." Don't fabricate.

## Failure handling

- If `period_end` can't be resolved from the user's phrasing, ask for an explicit date instead of guessing.
- If the Model Context Protocol server isn't registered or the tool raises, surface verbatim.
