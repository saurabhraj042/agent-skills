---
name: folder-organizer
description: Organize any messy folder (Downloads, Desktop, Documents, video footage, photos, PDFs) into clean buckets, safely, on Mac or Windows. Asks which folder, shows a dry-run plan, moves only after approval, and can undo. Use when the user says "organize / sort / clean up my folder", "my Downloads is a mess", or wants footage sorted.
---

# Folder Organizer

Sorts any folder into buckets. Scripts do the bulk work by rules; Claude only looks at the files the rules cannot place (for example, what is in a video). Everything is a dry run first, journaled, and undoable. Nothing is ever deleted.

Script: `scripts/organize.py` (Python 3.8+, standard library only). Run it with `python3` on Mac/Linux and `py -3` (or `python`) on Windows. Below, `ORG` means that command plus the script path.

Optional, auto-detected: `ffmpeg`/`ffprobe` (video details and contact sheets), `pdftotext` (PDF previews). Without them it still works, just with less detail for videos.

## Workflow

1. **Ask which folder.** If the user has not said, run `ORG where` and offer the common folders it lists (Downloads, Desktop, Documents, Movies or Videos, Pictures). Never pick for them. Never organize the home folder or a system folder; the script refuses.
2. **Ask which preset** (run `ORG presets`):
   - `general`: everyday sort (Images, Videos, PDFs, Documents, Installers, Archives, Screenshots...).
   - `creator`: video footage (Exports, Screen Recordings, Footage by what is in it, Thumbnails, Audio, Project Files).
   - a custom taxonomy file the user supplies (`--taxonomy file.json`; format in `taxonomy.json`).
   Also ask: move or copy (`--copy`), and whether to include sub-folders (`--recursive`). Default is move, top level only.
3. **Plan (dry run).** `ORG plan "<folder>" --preset <name> [--recursive] [--copy]`. Nothing moves. It prints files per bucket, duplicates, skipped files, and how many need a look.
4. **Review the files the rules could not place.** If the plan says "Needs a look" > 0:
   - Run `ORG peek "<folder>"`. It writes `.organizer/peek.json` (a contact sheet image for each video, a small image for each photo, first-page text for documents).
   - Read `.organizer/review.json` for the allowed buckets (`ai_buckets`) and the list. For each file, open the image with the Read tool (or read the text) and choose the best bucket. Choose from `ai_buckets` when present; otherwise use a sensible existing bucket name. If unsure, leave it out so it lands in `_Review`.
   - Write `decisions.json` outside the target folder: `{"relative/path.mp4": {"bucket": "Footage/B-roll/Gym", "note": "one-line description of what is in it", "tags": ["gym", "deadlift"]}}`. The `note` and `tags` go into the searchable catalog.
   - Re-run the plan with `--decisions decisions.json`.
5. **Show the user the plan summary** (buckets with counts, duplicates, skipped, anything in `_Review`). Say plainly that files will be moved (or copied). **Wait for a clear yes.**
6. **Apply.** Only after the yes: `ORG apply "<folder>" --yes`. Report counts, where the catalog is, and how to undo.
7. **Undo on request.** `ORG undo "<folder>"` restores every file from the latest journal and removes the folders it created if empty.

## Rules Claude must follow

- Never run `apply --yes` without the user's explicit approval of that plan in this conversation. Re-plan if the folder changed or the user changes the preset.
- Never delete anything. Exact duplicates go to `_Duplicates`; the user decides what to do with them.
- Unfinished downloads (`.crdownload`, `.part`), hidden/system files, symlinks, and project folders (anything with `.git`, `package.json`, app bundles, editing libraries) are left alone by design. Tell the user what was skipped.
- Do not read personal documents beyond what `peek` extracts. Previews are for filing only; do not repeat their contents back unless asked.
- Large folders: run `plan` on a sub-folder first if there are thousands of files and the user wants to test.
- Everything the script writes lives in `<folder>/.organizer/` (plan, review, peek images, journals, catalog).

## The catalog (for creators)

After `apply`, `.organizer/catalog.json` maps each file's new path to its bucket, size, video details (duration, resolution, orientation, fps), and the `note`/`tags` from Claude's review. In later sessions, use it to answer requests like "find my gym clips" or "which vertical clips are over 10 seconds" without re-scanning.

## Customizing buckets

Edit a copy of `taxonomy.json`. Buckets are checked top to bottom, first match wins. Rule keys: `ext`, `kind`, `name_regex`, `min_size_mb`, `max_size_mb`, `older_than_days`, and for video `orientation`, `min_height`, `min_duration`, `max_duration`. Bucket keys: `name` (use `/` for sub-folders), `group_by: "month"`, `ask_claude: true`. When the user corrects a placement, offer to add a rule for it in their custom taxonomy so it is automatic next time.

## Platform notes

- macOS: `~/Downloads`, `~/Desktop`, `~/Documents`, `~/Movies` may ask for folder permission the first time.
- Windows: works with drive paths like `C:\Users\<name>\Downloads`; quote paths with spaces; long paths and reserved names (CON, NUL...) are handled.
- File and folder names are made safe for both systems; name clashes get ` (1)`, ` (2)`.
