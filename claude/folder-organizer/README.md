# folder-organizer

A Claude skill that organizes any messy folder (Downloads, footage, photos, PDFs) on Mac and Windows.

- Asks which folder, then shows a **dry-run plan**. Nothing moves until you say yes.
- Rules sort the obvious files. Claude looks at the rest (for example, what is in a video) and files them by content.
- Every move is journaled. `undo` puts everything back. Nothing is ever deleted.
- Writes a searchable `catalog.json` (video duration, resolution, notes, tags) so Claude can find clips later.

## Install

```bash
cp -r claude/folder-organizer ~/.claude/skills/        # macOS / Linux
```
```powershell
Copy-Item -Recurse claude\folder-organizer $env:USERPROFILE\.claude\skills\   # Windows
```

Then tell Claude: "organize my Downloads folder" or "sort my footage folder".

Requires Python 3.8+. Optional: `ffmpeg` (video details and previews), `pdftotext` (PDF previews).

## Use it directly

```bash
python3 scripts/organize.py where
python3 scripts/organize.py plan ~/Downloads --preset general        # dry run
python3 scripts/organize.py apply ~/Downloads --yes                  # after you approve
python3 scripts/organize.py undo ~/Downloads
```
On Windows use `py -3 scripts\organize.py ...`.

## Presets

| Preset | For |
| ------ | --- |
| `general` | Everyday folders: Images, Videos, PDFs, Documents, Installers, Archives, Screenshots |
| `creator` | Footage: Exports, Screen Recordings, Talking-head, B-roll (gym, travel, desk), Thumbnails, Audio, Project Files |

Make your own: copy `taxonomy.json`, edit the buckets, and pass `--taxonomy my.json`.

## Safety

Dry run by default, `--yes` required to apply, hidden/system/unfinished files skipped, project folders and app bundles untouched, exact duplicates moved to `_Duplicates` (never deleted), home and system folders refused.
