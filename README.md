<div align="center">

# 🧠 Agent Skills

**A growing collection of reusable skills for AI coding agents.**

Teach your agent new tricks: package workflows, domain knowledge, and tooling into drop-in skills.

![Status](https://img.shields.io/badge/status-work%20in%20progress-blue)
![Claude Code](https://img.shields.io/badge/built%20for-Claude%20Code-orange)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

</div>

---

## ✨ What is this?

Skills are small, self-contained folders of instructions (and optional scripts or resources) that an AI agent loads on demand. Instead of re-explaining a workflow every session, you write it once as a skill and the agent picks it up whenever the task matches.

This repository is a home for skills I build and use day to day, shared so you can use, fork, and remix them.

## 🚀 Quick start

1. **Clone the repo**
   ```bash
   git clone git@github.com:saurabhraj042/agent-skills.git
   ```
2. **Copy a skill into your skills directory**
   ```bash
   cp -r agent-skills/claude/<skill-name> ~/.claude/skills/
   ```
3. **Use it.** Ask your agent for something the skill covers, or invoke it directly with `/<skill-name>`.

## 📦 Anatomy of a skill

```
my-skill/
├── SKILL.md        # Required: frontmatter (name, description) + instructions
├── scripts/        # Optional: helper scripts the skill can run
└── references/     # Optional: docs the agent reads when needed
```

A minimal `SKILL.md`:

```markdown
---
name: my-skill
description: Use when the user asks for X. Triggers on "do X", "run X".
---

# My Skill

Step-by-step instructions for the agent...
```

The `description` is what the agent uses to decide when to load the skill, so make it specific.

## 🗂️ Skills

More skills are added over time. Watch the repo to get notified.

| Skill | What it does |
| ----- | ------------ |
| [🎬 reel-competitor-teardown](claude/reel-competitor-teardown) | View-only analysis of one Instagram creator's reels and posts, producing a designed report with hook and caption patterns and a playbook. |

## 🤝 Contributing

Ideas, fixes, and new skills are welcome.

1. Fork the repo
2. Create a branch: `git checkout -b feat/my-skill`
3. Add your skill in its own folder with a clear `SKILL.md`
4. Open a pull request

Please make sure skills contain no secrets, API keys, or personal data.

## 📄 License

Released under the [MIT License](LICENSE).

---

<div align="center">

Made by [@saurabhraj042](https://github.com/saurabhraj042). If this is useful, a ⭐ is appreciated.

</div>
