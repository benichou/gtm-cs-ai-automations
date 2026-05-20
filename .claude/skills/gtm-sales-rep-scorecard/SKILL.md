---
name: gtm-sales-rep-scorecard
description: Generate a per-AE scorecard summarizing each rep's pipeline contribution and hygiene signals for a sales leader. Trigger when the user asks "how are my reps doing", "show me a rep scorecard", "pipeline by rep / by owner / by AE", "who's at risk on their number", "rep performance roll-up", "coaching opportunities", or "where do I need to coach".
---

# gtm-sales-rep-scorecard skill

Show how each AE is contributing to pipeline and where the hygiene signals are weakest. Calls the `roll_up_by_owner` tool on the `gtm-sales-leadership` Model Context Protocol server.

## When to use

Trigger phrases include:
- "How are my reps doing?"
- "Pipeline by owner / by rep / by AE"
- "Show me a rep scorecard"
- "Who's at risk on their number?"
- "Where do I need to coach?"
- "Rep performance roll-up"

Do NOT use for deal-level inspection (use `gtm-sales-at-risk`) or the overall forecast number (use `gtm-sales-forecast`).

## Steps

1. **Call** `roll_up_by_owner()` — no arguments.

2. **Format the response** exactly like this:

   ```
   ## Rep scorecard — as of <as_of>

   <For each owner, sorted by weighted_arr desc:>
   ### <owner_name> — $<weighted_arr> weighted · $<raw_arr> raw · <deals> deals
   - Commit $<commit_arr> · Best Case $<best_case_arr>
   - Late-stage deals (Proposal/Negotiation): <late_stage_deals>
   - Risk signals: <stale_deals> stale · <overdue_deals> overdue · <zero_activity_deals> with no activity logged
   ```

   Format ARR with commas.

3. **End with one coaching observation** grounded in the deltas — e.g. "M. Singh has the highest stale ratio (4 of 12 deals). Worth a Monday coaching mention." or "J. Torres carries 11 of 13 late-stage deals — concentration risk if they take vacation." Don't fabricate; only call out patterns the numbers actually support.

## Failure handling

- If the Model Context Protocol server isn't registered, the tool won't be callable. Tell the user to add `gtm-sales-leadership` to their `.claude/settings.json`.
- If the tool raises, surface verbatim.
