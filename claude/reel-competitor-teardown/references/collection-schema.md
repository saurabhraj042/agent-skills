# Collection schema (Phase 3: data collection)

Output of this phase: one `data.json` per account. Collection records what was SEEN. It never interprets.
Interpretation lives in `analysis-template.md`.

## Ground rules
- View only. No likes, follows, comments, saves, DMs, no typing credentials. The person logs in.
- Paraphrase, never copy. Fields marked `paraphrase` hold Claude's own short description of intent. No verbatim hooks, caption lines or on-screen text. Hashtags and keyword CTAs may be recorded as counts and types, not as copied blocks.
- Every field carries a source tag, recorded once per item in `src`:
  - `seen`: read directly from the page or a frame
  - `derived`: computed from seen fields
  - `unverified`: not observed (spoken words, anything behind a failed load)
- If a field could not be read, set it to `null` and add its name to `gaps`. Never guess.

## Sets to collect
| Set | Rule | Size |
|---|---|---|
| `viral` | Top reels by views from the Reels grid. Grid is not sorted by views, so sort yourself. Exclude collabs. | 10 |
| `recent` | Newest reels by date, excluding collabs. | 10 |
| posts | Newest non-reel posts (photo, carousel) from the main grid. | up to 10 |
A reel in both sets gets `"sets": ["viral","recent"]` and is stored once.

## Step order
1. Verify the account: after the person signs in, open `instagram.com/<handle>/`, confirm the handle and display name match what the person asked for, and read the profile. If it does not match, stop and ask.
2. Profile block (below).
3. Reels grid: `instagram.com/<handle>/reels/`. Map each `a[href*="/reel/"]` to its view-count text. Build the viral and recent sets.
4. Main grid: `instagram.com/<handle>/`. Anything whose href contains `/p/` is a post. Record type from the aria label or the carousel icon.
5. Open each item permalink once and extract (recipes below). Pace the navigation. One permalink at a time.
6. Frame sampling for reels only.
7. Write `data.json`, list `gaps`, hand over to analysis.

## Profile block
| Field | How | Source |
|---|---|---|
| handle, display_name | page text | seen |
| followers, following, posts_count | page text (parse K/M) | seen |
| bio_summary | paraphrase of the bio, 1 to 2 lines | seen |
| positioning | one phrase: who they say they are and for whom | seen |
| pillars | content themes inferred only from bio plus highlights | derived |
| link_type | none / form / chat-group / site / store | seen |
| category_label | label above bio if present | seen |
| highlights | list of highlight titles (count and themes only) | seen |
| verified_badge | boolean | seen |
| account_url_checked | true after step 1 | seen |

## Reel item
| Field | Recipe | Source |
|---|---|---|
| id, url | shortcode from href | seen |
| collab | final URL handle differs from the account (redirect) | seen |
| sets | viral, recent or both | derived |
| views | grid text on the Reels grid (permalink page does not show it) | seen |
| likes, comments | start of `og:description` ("N likes, M comments") | seen |
| posted_at | `time[datetime]` | seen |
| duration_s | `video.duration` | seen |
| audio.type | label has "Original audio" = original, else licensed | seen |
| audio.label | audio label text, or the title of `/reels/audio/<id>/` when the link text is empty | seen |
| audio.usage_count | "N reels" on the audio page | seen |
| caption_full_words | word count of `og:title` content | derived |
| caption.opening_type | classify the first line (see taxonomy in analysis template) | derived |
| caption.cta_type | keyword-comment / follow / save-share / link-in-bio / question / none | derived |
| caption.cta_keyword_used | boolean | seen |
| caption.hashtag_count, hashtag_layout | counts and layout description (blocks, mixed plain and #) | seen |
| caption.structure | ordered list of caption parts as labels (cta, reaction, analogy, list, credibility, stakes) | derived |
| hook.paraphrase | one line, own words | seen |
| hook.class | from taxonomy | derived |
| hook.overlay_words | word count of the first-second overlay | seen |
| hook.first_second_visual | face / notebook / screen / b-roll / text-only | seen |
| format.visual_setup, format.overlay_style | taxonomy, plus position and static vs switching | seen |
| spoken.status | `unverified` unless a transcript was supplied | unverified |
| spoken.hook_paraphrase | only if a transcript was supplied | seen |

## Post item (non-reel)
Fields: `id, url, type (photo | carousel | other), slides (carousel only), likes, comments, posted_at, caption_words, hashtag_count, topic (paraphrase), cta_type, collab`. Views are not shown for posts. `likes` and `comments` come from `og:description`, same recipe.

## Frame sampling (reels)
Pause and mute the video, seek to 0.4s, 25%, 50% and 75% of `duration_s`, wait about 700ms, screenshot at scale 0.5. Read overlay text for word count and style only, record in own words. Per reel this is 4 screenshots, so reduce to 0.4s plus one mid frame when the set is large.

## `data.json` shape
```json
{
  "meta": { "handle": "", "analysed_at": "YYYY-MM-DD", "source": "built-in browser, view only",
            "reels_viewed": 0, "posts_viewed": 0, "collabs_excluded": 0,
            "spoken_status": "not verified", "gaps": [] },
  "profile": { },
  "reels": [ ],
  "posts": [ ]
}
```

## Failure handling
- Page text sparse or the tab title is just "Instagram": the page has not loaded. Re-read before recording.
- Login wall or challenge page: stop and tell the person. Do not retry in a loop.
- A field that fails twice is recorded as `null` and listed in `meta.gaps`.
