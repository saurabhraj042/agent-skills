#!/usr/bin/env python3
"""folder-organizer: where -> plan -> (peek/decisions) -> plan -> apply -> undo.

Standard library only. Works on macOS, Windows and Linux (Python 3.8+).
Optional: ffmpeg/ffprobe (video details + contact sheets), pdftotext (PDF peek).

Nothing is moved by `plan`. `apply` needs --yes. Everything `apply` does is
journaled so `undo` can put every file back. Nothing is ever deleted.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TAXONOMY = HERE.parent / "taxonomy.json"
STATE_DIR = ".organizer"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif", ".bmp", ".tif", ".tiff",
             ".raw", ".cr2", ".cr3", ".nef", ".arw", ".dng"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".mts", ".m2ts", ".mxf", ".braw", ".wmv", ".flv", ".3gp"}
AUDIO_EXT = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".opus", ".aiff", ".wma"}
ARCHIVE_EXT = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz"}
DOC_EXT = {".pdf", ".doc", ".docx", ".rtf", ".odt", ".pages", ".txt", ".md", ".xls", ".xlsx", ".csv",
           ".ppt", ".pptx", ".key", ".epub"}

SKIP_FILES = {".ds_store", "thumbs.db", "desktop.ini", ".localized", "icon\r"}
SKIP_EXT = {".crdownload", ".part", ".download", ".partial", ".opdownload", ".tmp", ".swp", ".lock"}
PROTECTED_DIR_EXT = {".app", ".photoslibrary", ".fcpbundle", ".imovielibrary", ".xcodeproj", ".xcworkspace",
                     ".lrlibrary", ".logicx", ".band"}
PROJECT_MARKERS = {".git", "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "node_modules", "pom.xml"}
WIN_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
SPECIAL_BUCKETS = ("_Review", "_Duplicates")


# ----------------------------------------------------------------------------- helpers
def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def human(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def lp(path):
    """Windows long-path safe string."""
    s = str(path)
    if os.name == "nt" and len(s) > 240 and not s.startswith("\\\\?\\"):
        s = "\\\\?\\" + os.path.abspath(s)
    return s


def safe_part(part):
    part = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", part).strip().rstrip(". ")
    if not part:
        part = "_"
    if part.lower() in WIN_RESERVED:
        part = "_" + part
    return part


def safe_bucket(bucket):
    return "/".join(safe_part(p) for p in bucket.replace("\\", "/").split("/") if p)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        die(f"cannot read {path}: {exc}")


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def which(name):
    return shutil.which(name)


def run(cmd, timeout=60):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:  # noqa: BLE001
        return None


def kind_of(ext):
    if ext in IMAGE_EXT:
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in ARCHIVE_EXT:
        return "archive"
    if ext in DOC_EXT:
        return "document"
    return "other"


# ----------------------------------------------------------------------------- taxonomy
def load_preset(taxonomy_path, preset):
    tax = load_json(taxonomy_path or DEFAULT_TAXONOMY)
    if "buckets" in tax:  # a custom file that is itself one preset
        return tax
    presets = tax.get("presets", {})
    if preset not in presets:
        die(f"unknown preset '{preset}'. Available: {', '.join(presets)}")
    return presets[preset]


def bucket_roots(preset):
    roots = {safe_bucket(b["name"]).split("/")[0] for b in preset["buckets"]}
    roots.update(safe_bucket(b).split("/")[0] for b in preset.get("ai_buckets", []))
    roots.update(SPECIAL_BUCKETS)
    return roots


def rule_matches(rule, e):
    if "ext" in rule and e["ext"] not in rule["ext"]:
        return False
    if "kind" in rule and e["kind"] != rule["kind"]:
        return False
    if "name_regex" in rule and not re.search(rule["name_regex"], e["name"], re.I):
        return False
    mb = e["size"] / (1024 * 1024)
    if "min_size_mb" in rule and mb < rule["min_size_mb"]:
        return False
    if "max_size_mb" in rule and mb > rule["max_size_mb"]:
        return False
    if "older_than_days" in rule and (datetime.now().timestamp() - e["mtime"]) / 86400 < rule["older_than_days"]:
        return False
    vr = rule.get("video")
    if vr:
        m = e.get("meta") or {}
        if e["kind"] != "video":
            return False
        for key, want in vr.items():
            if key == "orientation":
                if m.get("orientation") != want:
                    return False
            elif key == "min_height" and not (m.get("height") and m["height"] >= want):
                return False
            elif key == "max_height" and not (m.get("height") and m["height"] <= want):
                return False
            elif key == "min_duration" and not (m.get("duration") is not None and m["duration"] >= want):
                return False
            elif key == "max_duration" and not (m.get("duration") is not None and m["duration"] <= want):
                return False
    return True


def classify(e, preset):
    for b in preset["buckets"]:
        if any(rule_matches(r, e) for r in b["rules"]):
            return b
    return None


# ----------------------------------------------------------------------------- probing
def probe_video(path):
    if not which("ffprobe"):
        return {}
    res = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
               "stream=width,height,r_frame_rate:stream_tags=rotate:stream_side_data=rotation:format=duration:format_tags=creation_time",
               "-of", "json", str(path)])
    if not res or res.returncode != 0:
        return {}
    try:
        d = json.loads(res.stdout)
        s = (d.get("streams") or [{}])[0]
        w, h = int(s.get("width", 0)), int(s.get("height", 0))
        rot = s.get("tags", {}).get("rotate")
        for sd in s.get("side_data_list", []) or []:
            rot = sd.get("rotation", rot)
        if rot is not None and abs(int(float(rot))) in (90, 270):
            w, h = h, w
        fr = s.get("r_frame_rate", "0/1").split("/")
        fps = round(int(fr[0]) / int(fr[1]), 2) if len(fr) == 2 and int(fr[1]) else None
        dur = d.get("format", {}).get("duration")
        meta = {"width": w, "height": h, "fps": fps,
                "duration": round(float(dur), 2) if dur else None,
                "orientation": "portrait" if h > w else "landscape" if w > h else "square"}
        ct = d.get("format", {}).get("tags", {}).get("creation_time")
        if ct:
            meta["created"] = ct[:10]
        return meta
    except Exception:  # noqa: BLE001
        return {}


# ----------------------------------------------------------------------------- scan
def is_project_dir(p):
    try:
        names = set(os.listdir(p))
    except OSError:
        return True
    return bool(names & PROJECT_MARKERS) or any(n.endswith(".xcodeproj") for n in names)


def scan(root, recursive, preset, probe):
    entries, skipped = [], []
    roots = bucket_roots(preset)

    def consider(fpath, rel):
        name = fpath.name
        ext = fpath.suffix.lower()
        if name.startswith(".") or name.lower() in SKIP_FILES:
            skipped.append({"src": rel, "reason": "hidden/system file"})
            return
        if ext in SKIP_EXT:
            skipped.append({"src": rel, "reason": "unfinished download/temp file"})
            return
        if fpath.is_symlink():
            skipped.append({"src": rel, "reason": "symlink"})
            return
        try:
            st = fpath.stat()
        except OSError:
            skipped.append({"src": rel, "reason": "unreadable"})
            return
        e = {"rel": rel, "name": name, "ext": ext, "kind": kind_of(ext), "size": st.st_size,
             "mtime": st.st_mtime, "meta": {}}
        if probe and e["kind"] == "video":
            e["meta"] = probe_video(fpath)
        entries.append(e)

    if not recursive:
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            rel = child.name
            if child.is_dir():
                continue
            consider(child, rel)
    else:
        for dirpath, dirnames, filenames in os.walk(root):
            here = Path(dirpath)
            depth_rel = here.relative_to(root)
            keep = []
            for d in sorted(dirnames):
                dp = here / d
                top = (depth_rel.parts[0] if depth_rel.parts else d)
                if d.startswith(".") or Path(d).suffix.lower() in PROTECTED_DIR_EXT or top in roots:
                    continue
                if is_project_dir(dp):
                    skipped.append({"src": str(depth_rel / d).replace("\\", "/") + "/", "reason": "project/app folder left alone"})
                    continue
                keep.append(d)
            dirnames[:] = keep
            if depth_rel.parts and depth_rel.parts[0] in roots:
                continue
            for f in sorted(filenames):
                rel = str((depth_rel / f)).replace("\\", "/") if depth_rel.parts else f
                consider(here / f, rel)
    return entries, skipped


def file_hash(path):
    h = hashlib.sha256()
    with open(lp(path), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------------- root safety
def resolve_root(folder, force=False):
    root = Path(os.path.expanduser(folder)).resolve()
    if not root.is_dir():
        die(f"not a folder: {root}")
    home = Path.home().resolve()
    danger = {home, Path(root.anchor)}
    for p in ("/System", "/Library", "/usr", "/bin", "/etc", "/Applications", "/private",
              "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)", "C:\\ProgramData"):
        danger.add(Path(p))
    if root in danger and not force:
        die(f"refusing to organize {root} (system or home root). Pick a sub-folder like Downloads.")
    return root


# ----------------------------------------------------------------------------- commands
def cmd_where(_a):
    home = Path.home()
    cands = ["Downloads", "Desktop", "Documents", "Movies", "Videos", "Pictures", "Music"]
    print(f"Platform: {sys.platform} | Home: {home}")
    for c in cands:
        p = home / c
        if p.is_dir():
            try:
                n = sum(1 for x in p.iterdir() if x.is_file() and not x.name.startswith("."))
            except OSError:
                n = "?"
            print(f"  {p}   ({n} loose files)")


def cmd_presets(a):
    tax = load_json(a.taxonomy or DEFAULT_TAXONOMY)
    for name, p in tax.get("presets", {}).items():
        print(f"{name}: {p.get('description', '')}")
        print("   buckets: " + ", ".join(b["name"] for b in p["buckets"]))


def cmd_plan(a):
    root = resolve_root(a.folder, a.force_root)
    preset = load_preset(a.taxonomy, a.preset)
    entries, skipped = scan(root, a.recursive, preset, not a.no_probe)
    decisions = load_json(a.decisions) if a.decisions else {}
    by_name = {b["name"]: b for b in preset["buckets"]}
    state = root / STATE_DIR

    def dest_dir(bucket_name, e, group):
        parts = safe_bucket(bucket_name)
        if group == "month":
            d = (e.get("meta") or {}).get("created") or datetime.fromtimestamp(e["mtime"]).strftime("%Y-%m-%d")
            parts += "/" + d[:7]
        return parts

    items = []
    for e in entries:
        b = classify(e, preset)
        d = decisions.get(e["rel"]) or {}
        if d.get("bucket"):
            bucket, conf = d["bucket"], "claude"
            group = (by_name.get(bucket) or {}).get("group_by")
            reason = d.get("note") or "chosen by Claude after looking at the file"
        elif b:
            bucket, conf, group = b["name"], "rule", b.get("group_by")
            reason = f"matched '{b['name']}' rule"
        else:
            bucket, conf, group, reason = "_Review", "unmatched", None, "no rule matched"
        items.append({"src": e["rel"], "bucket": bucket, "dst_dir": dest_dir(bucket, e, group), "conf": conf,
                      "reason": reason, "size": e["size"], "kind": e["kind"], "mtime": e["mtime"],
                      "meta": e["meta"], "note": d.get("note"), "tags": d.get("tags"),
                      "ask": bool(b and b.get("ask_claude") and not d.get("bucket")) or (b is None and not d.get("bucket"))})

    # exact duplicates: same size, then same sha256. Oldest copy stays, others -> _Duplicates (never deleted)
    if not a.no_dedupe:
        by_size = {}
        for it in items:
            if it["size"] >= 1024:  # tiny files are not worth flagging
                by_size.setdefault(it["size"], []).append(it)
        for group in by_size.values():
            if len(group) < 2:
                continue
            hashed = {}
            for it in group:
                try:
                    hashed.setdefault(file_hash(root / it["src"]), []).append(it)
                except OSError:
                    pass
            for same in hashed.values():
                if len(same) < 2:
                    continue
                same.sort(key=lambda x: (x["mtime"], len(x["src"])))
                for dup in same[1:]:
                    dup.update(bucket="_Duplicates", dst_dir="_Duplicates", conf="duplicate", ask=False,
                               reason=f"exact copy of {same[0]['src']}")

    # destinations, collision-safe (case-insensitive so Windows/macOS behave)
    taken = set()
    moves = []
    for it in items:
        name = safe_part(Path(it["src"]).name)
        dst_rel = f"{it['dst_dir']}/{name}"
        if dst_rel.lower() == it["src"].lower():
            continue  # already in place
        stem, suf, n = Path(name).stem, Path(name).suffix, 0
        while dst_rel.lower() in taken or (root / dst_rel).exists():
            n += 1
            dst_rel = f"{it['dst_dir']}/{stem} ({n}){suf}"
        taken.add(dst_rel.lower())
        it["dst"] = dst_rel
        moves.append(it)

    review = [{"src": m["src"], "kind": m["kind"], "default_bucket": m["bucket"], "size": human(m["size"]),
               "meta": m["meta"]} for m in moves if m["ask"]]
    plan = {"root": str(root), "preset": a.preset, "created": datetime.now().isoformat(timespec="seconds"),
            "mode": "copy" if a.copy else "move", "recursive": a.recursive, "moves": moves,
            "skipped": skipped, "ai_buckets": preset.get("ai_buckets", [])}
    write_json(state / "plan.json", plan)
    write_json(state / "review.json", {"ai_buckets": preset.get("ai_buckets", []), "items": review})

    summary = {}
    for m in moves:
        s = summary.setdefault(m["bucket"], [0, 0])
        s[0] += 1
        s[1] += m["size"]
    print(f"Folder: {root}\nPreset: {a.preset} | mode: {plan['mode']} | files planned: {len(moves)} | skipped: {len(skipped)}")
    for b, (cnt, sz) in sorted(summary.items(), key=lambda kv: -kv[1][0]):
        print(f"  {b:<34} {cnt:>5} files  {human(sz):>10}")
    dups = sum(1 for m in moves if m["conf"] == "duplicate")
    if dups:
        print(f"Exact duplicates found: {dups} (moved to _Duplicates, never deleted)")
    if skipped:
        reasons = {}
        for s in skipped:
            reasons[s["reason"]] = reasons.get(s["reason"], 0) + 1
        print("Skipped: " + "; ".join(f"{v} {k}" for k, v in reasons.items()))
    print(f"Needs a look (Claude/you): {len(review)} -> {state / 'review.json'}")
    print(f"Plan saved: {state / 'plan.json'}  (DRY RUN - nothing has moved)")


def media_to_jpg(src, out, scale="scale=-2:360"):
    return bool(which("ffmpeg")) and (run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", scale, "-frames:v", "1", str(out)]) or
                                      subprocess.CompletedProcess([], 1)).returncode == 0


def docx_text(path, limit=600):
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf8", "ignore")
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", xml)).strip()[:limit]
    except Exception:  # noqa: BLE001
        return ""


def cmd_peek(a):
    root = resolve_root(a.folder, a.force_root)
    state = root / STATE_DIR
    review = load_json(state / "review.json")
    out_dir = state / "peek"
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for i, it in enumerate(review["items"][: a.limit]):
        src = root / it["src"]
        kind, key = it["kind"], it["src"]
        if kind == "video" and which("ffmpeg"):
            dur = (it.get("meta") or {}).get("duration") or 3
            frames = []
            for j, frac in enumerate((0.15, 0.5, 0.85)):
                f = out_dir / f"{i:04d}_{j}.jpg"
                r = run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dur * frac:.2f}", "-i", str(src),
                         "-vf", "scale=-2:360", "-frames:v", "1", str(f)])
                if r and r.returncode == 0 and f.exists():
                    frames.append(f)
            if len(frames) == 3:
                sheet = out_dir / f"{i:04d}_sheet.jpg"
                cmd = ["ffmpeg", "-y", "-v", "error"]
                for f in frames:
                    cmd += ["-i", str(f)]
                cmd += ["-filter_complex", "hstack=inputs=3", str(sheet)]
                r = run(cmd)
                result[key] = {"type": "image", "file": str(sheet)} if r and r.returncode == 0 else {"type": "image", "file": str(frames[1])}
            elif frames:
                result[key] = {"type": "image", "file": str(frames[0])}
            else:
                result[key] = {"type": "none", "note": "could not extract frames"}
            for f in frames:
                if f.exists() and result[key].get("file") != str(f):
                    f.unlink()  # our own temp frame
        elif kind == "image":
            small = out_dir / f"{i:04d}.jpg"
            result[key] = {"type": "image", "file": str(small)} if media_to_jpg(src, small, "scale='min(640,iw)':-2") else {"type": "image", "file": str(src)}
        elif kind == "document":
            text = ""
            ext = Path(key).suffix.lower()
            if ext == ".pdf" and which("pdftotext"):
                r = run(["pdftotext", "-l", "1", str(src), "-"])
                text = (r.stdout if r else "")[:600]
            elif ext == ".docx":
                text = docx_text(src)
            elif ext in (".txt", ".md", ".csv", ".tsv", ".srt", ".vtt"):
                text = src.read_text(encoding="utf-8", errors="ignore")[:600]
            result[key] = {"type": "text", "text": re.sub(r"\s+", " ", text).strip()} if text else {"type": "none", "note": "no preview available"}
        else:
            result[key] = {"type": "none", "note": f"{kind} file, judge by name: {Path(key).name}"}
    write_json(state / "peek.json", result)
    print(f"Peek written for {len(result)} files -> {state / 'peek.json'}")


def cmd_apply(a):
    root = resolve_root(a.folder, a.force_root)
    state = root / STATE_DIR
    plan = load_json(state / "plan.json")
    if not a.yes:
        die("dry run only. Re-run with --yes AFTER the user has approved the plan.")
    mode = plan["mode"]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    journal = {"root": str(root), "mode": mode, "started": stamp, "ops": [], "created_dirs": []}
    taken, done, stale = set(), 0, 0
    try:
        for m in plan["moves"]:
            src, dst = root / m["src"], root / m["dst"]
            if not src.exists() or src.stat().st_size != m["size"]:
                stale += 1
                print(f"  skip (changed since plan): {m['src']}")
                continue
            n, stem, suf = 0, dst.stem, dst.suffix
            while dst.exists() or str(dst).lower() in taken:
                n += 1
                dst = dst.with_name(f"{stem} ({n}){suf}")
            taken.add(str(dst).lower())
            parent = dst.parent
            missing = []
            p = parent
            while not p.exists() and p != root:
                missing.append(str(p))
                p = p.parent
            parent.mkdir(parents=True, exist_ok=True)
            journal["created_dirs"] += list(reversed(missing))
            if mode == "copy":
                shutil.copy2(lp(src), lp(dst))
            else:
                shutil.move(lp(src), lp(dst))
            journal["ops"].append({"src": str(src), "dst": str(dst), "size": m["size"]})
            done += 1
    finally:
        write_json(state / f"journal-{stamp}.json", journal)
        catalog_path = state / "catalog.json"
        catalog = load_json(catalog_path) if catalog_path.exists() else {"root": str(root), "files": {}}
        by_dst = {o["src"]: o["dst"] for o in journal["ops"]}
        for m in plan["moves"]:
            final = by_dst.get(str(root / m["src"]))
            if final:
                rel = os.path.relpath(final, root).replace("\\", "/")
                catalog["files"][rel] = {"bucket": m["bucket"], "kind": m["kind"], "size": m["size"],
                                         "meta": m.get("meta") or {}, "note": m.get("note"), "tags": m.get("tags"),
                                         "original_name": Path(m["src"]).name, "organized": stamp}
        write_json(catalog_path, catalog)
    print(f"Done: {done} files {'copied' if mode == 'copy' else 'moved'}, {stale} skipped (changed).")
    print(f"Undo any time:  organize.py undo \"{root}\"")
    print(f"Searchable catalog: {state / 'catalog.json'}")


def cmd_undo(a):
    root = resolve_root(a.folder, a.force_root)
    state = root / STATE_DIR
    journals = sorted(state.glob("journal-*.json"))
    if not journals:
        die("no journal found: nothing to undo.")
    jpath = Path(a.journal) if a.journal else journals[-1]
    j = load_json(jpath)
    restored = 0
    for op in reversed(j["ops"]):
        src, dst = Path(op["src"]), Path(op["dst"])
        if not dst.exists():
            print(f"  missing, skipped: {dst}")
            continue
        if j["mode"] == "copy":
            if dst.stat().st_size == op["size"] and src.exists():
                dst.unlink()  # remove only our own copy, original is intact
                restored += 1
            continue
        target = src
        n = 0
        while target.exists():
            n += 1
            target = src.with_name(f"{src.stem} (restored {n}){src.suffix}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(lp(dst), lp(target))
        restored += 1
    for d in reversed(j.get("created_dirs", [])):
        try:
            os.rmdir(d)  # only removes if empty
        except OSError:
            pass
    jpath.rename(jpath.with_suffix(".undone.json"))
    print(f"Restored {restored} files from {jpath.name}.")


def main():
    ap = argparse.ArgumentParser(prog="organize.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("where", help="list common folders on this computer").set_defaults(fn=cmd_where)
    p = sub.add_parser("presets", help="list presets")
    p.add_argument("--taxonomy")
    p.set_defaults(fn=cmd_presets)

    def common(p):
        p.add_argument("folder")
        p.add_argument("--force-root", action="store_true", help="allow system/home roots (not recommended)")

    p = sub.add_parser("plan", help="scan + build a dry-run plan (moves nothing)")
    common(p)
    p.add_argument("--preset", default="general")
    p.add_argument("--taxonomy")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--copy", action="store_true", help="copy instead of move")
    p.add_argument("--decisions", help="JSON {relpath: {bucket, note, tags}} from Claude's review")
    p.add_argument("--no-dedupe", action="store_true")
    p.add_argument("--no-probe", action="store_true", help="skip ffprobe on videos")
    p.set_defaults(fn=cmd_plan)

    p = sub.add_parser("peek", help="make previews (contact sheets, text) for files that need a look")
    common(p)
    p.add_argument("--limit", type=int, default=60)
    p.set_defaults(fn=cmd_peek)

    p = sub.add_parser("apply", help="execute the saved plan (needs --yes)")
    common(p)
    p.add_argument("--yes", action="store_true")
    p.set_defaults(fn=cmd_apply)

    p = sub.add_parser("undo", help="put everything back from the latest journal")
    common(p)
    p.add_argument("--journal")
    p.set_defaults(fn=cmd_undo)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
