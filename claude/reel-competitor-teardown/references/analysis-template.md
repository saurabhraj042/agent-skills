# Analysis template (Phase 4)

Input: `data.json`. Output: the `analysis` block added to the same JSON, which the report template renders.
The report computes all numbers itself from the collected rows. Claude writes only the judgments below.

## Principles
- Small samples. n is usually 10 per set. Use medians, never means. Say "signal", never "proof".
- Every claim cites evidence: reel ids or a count ("6 of 10 viral reels").
- Confidence tag per takeaway: `high` (consistent in both sets and clear gap), `medium` (consistent in one set), `low` (suggestive only).
- No spoken-word claims unless a transcript was supplied. Say "spoken content not verified".
- Never copy wording. Describe structure.
- Separate what the creator does from why it works. The second is a hypothesis, and says so.

## Taxonomies (use these exact labels)
**Hook class**: `outcome-flex`, `life-after-knowing`, `struggle-to-lesson`, `time-compression`, `named-theory`, `identity-pov`, `contrarian-claim`, `curiosity-gap`, `tutorial-promise`, `other`.
**CTA type**: `keyword-comment`, `follow`, `save-share`, `link-in-bio`, `question`, `none`.
**Caption opening type**: `cta-first`, `reaction-line`, `story-open`, `claim-open`, `question-open`, `credibility-open`.
**Visual setup**: `selfie-talking`, `car-selfie`, `screen-recording`, `handwritten-notes`, `b-roll`, `text-only`, `voiceover-demo`.
**Duration bands**: `<=12s`, `13-30s`, `31-45s`, `>45s`.

## Computed by the report (do not hand-calculate)
- Medians: views, comments, comment rate (comments / views), likes rate, duration, caption words, hashtag count.
- Distribution of hook class, CTA type, visual setup, audio type per set.
- Median comment rate per hook class (with n).
- Breakout multiple: views / median views of the recent set.
- Posting cadence: recent reels per week from first to last date.
- Viral vs recent deltas.

## What Claude writes (analysis block)
```json
"analysis": {
  "verdict": "one sentence on what this account's engine is",
  "takeaways": [
    { "claim": "", "evidence": "", "confidence": "high|medium|low", "why_hypothesis": "" }
  ],
  "viral_vs_recent": "2 to 3 sentences: what changed between breakout and everyday content",
  "hook_notes": "2 sentences",
  "caption_notes": "2 sentences",
  "steal": ["structure-only item, no wording"],
  "avoid": ["item"],
  "tests": [ { "idea": "", "why": "", "metric": "" } ],
  "caveats": ["small sample", "spoken content not verified"]
}
```

## Judgment checklist (answer before writing)
1. Which hook class carries the highest median comment rate, and is the gap larger than the sample noise? If n < 3 for a class, mark `low`.
2. What do the 3 top reels share that the bottom 3 recent reels lack (setup, duration band, CTA, audio)?
3. Is the breakout tied to a topic, a format, or an audio? Check whether the same format underperformed elsewhere in the sets.
4. Are views driven by one outlier? If the top reel is more than 5x the second, say so.
5. Do posts (non-reels) show the same CTA and caption style, or a different one?
6. What would change the conclusion? Put it in `caveats`.

## Rules for `steal` and `tests`
- `steal`: structure only, for example "overlay stays static for the whole video" or "caption opens with the action line, then a reaction line". No quoted phrases.
- `tests`: each test is an A/B the person can run on their own account, names the metric to read, and is small (one reel).
- Everything must fit the person's own niche and guardrails. Do not suggest copying paid course material or unverifiable superiority claims.
