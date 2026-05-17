---
description: Repurpose a long-form marketing asset (blog post, webinar transcript) into 3 channel-specific outputs — LinkedIn post, sales one-pager, and customer email — with brand-voice scoring and an audit log
argument-hint: <path-to-asset>
---

I want to repurpose the marketing asset at **$1** into three channel-specific outputs:

1. A LinkedIn post (3-5 sentences, no emojis or hashtags)
2. A sales-enablement one-pager (one page, three sections: problem / solution / proof)
3. A customer email (subject line under 60 chars, 3-5 sentence body, plain language)

Please use the `marketing-repurpose` skill to:

- Call `extract_asset_text` on $1 to get the source text.
- Call `lookup_style_guide("tone")` and `lookup_style_guide("structure")` to learn the brand voice and the per-channel structure.
- Generate each artifact and write it to `output/<channel>.md`.
- After all three artifacts are written, chain into the `marketing-brand-audit` skill to score each one and report any artifacts below 0.7.

Every file write should trigger the PostToolUse audit hook automatically — no need to manually log anything.
