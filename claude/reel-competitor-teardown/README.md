# 🎬 Reel Competitor Teardown

**Study any Instagram creator's reels and posts, and get a designed, evidence-backed report on what makes their content work.**

Give your agent one handle. It browses the account **view-only** in your own signed-in browser, collects the data, analyses hooks, captions, formats and cadence, and builds a standalone HTML report with a playbook you can act on.

## ✨ What you get

A single-page report covering:

- **Profile snapshot**: positioning, bio, content pillars, link type, highlights
- **Most viral reels**: top 10 by views, with breakout multiples against the account's median
- **Last 10 reels**: what the creator is posting now, and posting cadence
- **Posts**: newest photo and carousel posts, up to 10
- **Hook patterns**: hook class distribution and median comment rate per class
- **Caption patterns**: opening type, CTA type, length, hashtag use
- **Viral vs recent**: what changed between breakout and everyday content
- **Playbook**: structures to borrow, things to avoid, and small A/B tests for your own account
- **Caveats**: sample size and unverified claims, stated plainly

Every takeaway cites reel ids or counts and carries a `high`, `medium` or `low` confidence tag.

## 🛡️ Guardrails

| Rule | What it means |
| ---- | ------------- |
| View only | Never likes, follows, comments, saves, shares or messages |
| You sign in | The agent never types, asks for or repeats credentials |
| One account per run | Extra handles are queued, not mixed in |
| No copied wording | Hooks, captions and on-screen text are paraphrased, and a check enforces it |
| No unverified claims | Spoken content is marked unverified unless you supply a transcript |
| Stops on friction | Login walls, checkpoints, rate limits and private accounts end collection |

## 🚀 Usage

1. Install the skill (see below).
2. Ask your agent something like:
   > Do a competitor teardown of @somecreator on Instagram
3. Sign in to Instagram in the browser when asked, then reply "done".
4. Receive the report plus a short chat summary: the verdict and the top 3 takeaways.

Works with a browser the agent can drive, such as the built-in browser pane or Claude in Chrome. A separate Instagram account for research is the cleaner choice.

## 📦 Install

```bash
cp -r claude/reel-competitor-teardown ~/.claude/skills/
```

## 🗂️ Structure

```
reel-competitor-teardown/
├── SKILL.md                        # Flow, hard rules, known behaviours
├── scripts/
│   └── build_report.py             # Injects data.json into the report template
└── references/
    ├── collection-schema.md        # What to collect and how
    ├── analysis-template.md        # Taxonomies and the analysis block
    ├── report-template.html        # The report page
    └── sample-data.json            # Fictional data for a layout preview
```

## 🔍 Preview the report layout

The sample data is fictional and lets you see the report without touching Instagram:

```bash
python3 scripts/build_report.py references/sample-data.json preview.html
open preview.html
```

Requires Python 3 and no extra packages.

## ⚠️ Limitations

- Samples are small (about 10 per set), so findings are signals, not proof. The report uses medians and says so.
- Audio is not heard, so spoken content stays unverified unless you provide a transcript.
- Collab reels are excluded because their permalinks redirect to the co-author.
- Views are shown only on reels. Posts have likes and comments only.
- Instagram's layout changes over time and may break some extraction steps.

## ⚖️ Responsible use

Only look at publicly visible content, follow Instagram's terms and local law, and use the findings to inform your own original work. Do not copy a creator's wording or paid material.
