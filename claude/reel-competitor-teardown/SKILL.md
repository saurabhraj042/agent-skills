---
name: reel-competitor-teardown
description: Analyse one Instagram creator's reels and posts, view only, and produce a designed report (profile, most viral reels, last 10 reels, posts, hook and caption patterns, playbook). Use when the person asks to analyse, tear down or study a creator or competitor account on Instagram.
---

# Reel competitor teardown

One account per run. The person signs in, Claude only looks. Output: a report page built from collected data.

## Hard rules
- **View only.** Never like, follow, comment, save, share, message, or change any setting.
- **The person signs in, not Claude.** Never type, ask for, or repeat a password or code. Never ask the person to paste credentials into the chat.
- **One account at a time.** If several handles are given, take the first, queue the rest, finish its report, then offer the next.
- **No copied wording.** Hooks, captions and on-screen text are described in Claude's own words. The check in step 6 enforces it.
- **No unverified claims.** Anything not seen is marked unverified. Spoken words are unverified unless a transcript was supplied.
- **Stop on friction.** A login wall, a challenge or checkpoint page, a rate-limit message, or a private account ends collection. Tell the person and wait. Do not retry in a loop.

## Files in this skill
- `references/collection-schema.md`: what to collect and how (read before step 4)
- `references/analysis-template.md`: taxonomies and the analysis block (read before step 6)
- `references/report-template.html`: the report page (filled by the script, never edited by hand)
- `scripts/build_report.py`: `python3 scripts/build_report.py data.json report.html`
- `references/sample-data.json`: fictional data for a layout preview

## Flow

### 1. Ask for the account
Ask for one Instagram handle or profile link. Normalise it to the bare handle. Do nothing else until it is given.

### 2. Browser and sign-in
- Use the browser the session prefers (the built-in browser pane or Claude in Chrome). Load that browser's own skill first and follow it for tabs, approvals and what the person can see.
- If neither browser is reachable, say so and stop.
- Open `instagram.com`. If it shows a login page, tell the person to sign in themselves in that browser (a separate account for research is the cleaner choice) and to reply "done" when finished. Make sure the browser pane is visible to them before asking.
- Do not continue until they confirm. If the page still shows a login form after "done", say so and ask again.

### 3. Verify the target account
Open `instagram.com/<handle>/`. Confirm the page shows that handle and a display name, plus followers, following and posts count. Tell the person in one line what you found ("@handle, Display Name, 14K followers"). Then:
- Not found, private account, or a different handle after redirect: stop and ask.
- Matches: continue.

### 4. Collect
Follow `references/collection-schema.md`. Targets:
1. **Profile and bio.**
2. **Most viral reels**: top 10 by views from the Reels grid, collabs excluded.
3. **Recent reels**: newest 10 by date, collabs excluded.
4. **Posts**: newest non-reel posts from the main grid, up to 10.
5. **Every item**: caption and hashtags, counts, date, duration (reels), audio (reels), hook, format.

Practical rules:
- The Reels grid is not sorted by views. Sort yourself.
- Open one permalink at a time, then extract with one script call. Do not open many tabs at once.
- Full captions come from the page metadata, so there is no need to click "more".
- Frame sampling (pause, mute, seek, screenshot) is for reading overlay text only.
- Write `data.json` as you go so a stop does not lose work.

When collection ends, tell the person in two lines what was collected and what could not be read.

### 5. Spoken content
Default: mark every reel's spoken content "not verified". Claude cannot hear audio. If the person supplies transcripts (their own screen recording run through a speech-to-text tool, or an output they pasted), add them to the matching reels and record only a paraphrased hook. Never invent or imply what was said.

### 6. Analyse
Follow `references/analysis-template.md`. Write the `analysis` block into `data.json`. Before building:
- **Wording check.** Read every paraphrase field (hook, topic, caption notes). None may reuse more than four consecutive words from the page. Rewrite any that do.
- **Evidence check.** Every takeaway names reel ids or a count. Anything resting on fewer than 3 items is `low`.
- **Honesty check.** The caveats list includes small sample size and unverified spoken content.

### 7. Build and deliver the report
1. `python3 scripts/build_report.py data.json report.html`
2. Publish `report.html` as a private artifact when an Artifact tool is available. Otherwise send the file.
3. In chat: one sentence on the account, the verdict, and the top 3 takeaways. Not the whole report.
4. Say that the report is private until shared.
5. Offer the next queued account, or ask whether to run another.

## Known behaviours (tested)
- Reel permalinks for collab posts redirect to the co-author's handle. Flag and exclude them.
- The `og:title` meta tag holds the full caption including the hashtag block. The `og:description` meta tag starts with likes and comments counts and the date.
- The audio link sometimes has empty text. Its URL ends in an audio id; open that audio page and read the track, artist and "N reels" count.
- The video is a blob with no caption track. Captions are not available from the page, and the page's security policy blocks sending audio elsewhere. Do not try to work around it.
- The pane is phone-sized. Prefer page text and script reads over screenshots.
- A tab titled just "Instagram" with sparse text means the page has not loaded. Read again before concluding.
- Views appear only on reels. Posts have likes and comments only.

## Failure and edge cases
- **2FA or checkpoint:** the person handles it in the browser, then says "done".
- **Account with fewer than 10 reels or posts:** collect what exists and state the real counts.
- **Account mostly collabs:** say so in the report's evidence section.
- **Non-English content:** analyse the structure and label hooks by class. Mark any language you could not read as unverified.
