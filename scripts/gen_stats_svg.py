# -*- coding: utf-8 -*-
"""Generate assets/github-stats.svg from live GitHub API data.

Usage:
    set GITHUB_TOKEN=ghp_xxx   (classic token with repo scope, or fine-grained with public repo read)
    python scripts/gen_stats_svg.py
Then commit the regenerated assets/github-stats.svg.
"""
import json
import os
import urllib.request

API = "https://api.github.com"
USER = "youbing-dev"
TOKEN = os.environ["GITHUB_TOKEN"]


def get(path):
    req = urllib.request.Request(API + path)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-stats-gen")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


profile = get(f"/users/{USER}")
repos = get(f"/users/{USER}/repos?per_page=100&sort=updated")
public_repos = profile.get("public_repos", len(repos))
stars = sum(r.get("stargazers_count", 0) for r in repos)
joined = (profile.get("created_at", "") or "")[:7].replace("-", ".")

lang_bytes = {}
for r in repos:
    if r.get("fork") or r.get("size", 0) == 0:
        continue
    try:
        langs = get(f"/repos/{USER}/{r['name']}/languages")
    except Exception:
        continue
    for k, v in langs.items():
        lang_bytes[k] = lang_bytes.get(k, 0) + v

total = sum(lang_bytes.values())
top = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:5]
lang_data = [(name, b / total * 100) for name, b in top]

LANG_COLORS = {
    "Java": "#b07219", "Python": "#3572A5", "Vue": "#41b883", "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#663399", "SCSS": "#c6538c",
    "Shell": "#89e051", "Dockerfile": "#384d54", "C++": "#f34b7d", "C": "#555555",
    "Go": "#00ADD8", "Rust": "#dea584", "Kotlin": "#A97BFF", "PHP": "#4F5D95",
}

BG, PANEL, BORDER = "#1a1b27", "#24283b", "#3b4261"
TXT, MUTED, BLUE, GREEN = "#e2e8f0", "#a9b1d6", "#70a5fd", "#9ece6a"
FONT = "Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"

W, H = 850, 300
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">',
    f'<rect x="0.5" y="0.5" rx="12" width="{W - 1}" height="{H - 1}" fill="{BG}" stroke="{BORDER}"/>',
    f'<rect x="30" y="24" width="4" height="22" rx="2" fill="{GREEN}"/>',
    f'<text x="44" y="42" font-family="{FONT}" font-size="19" font-weight="bold" fill="{TXT}">游冰 YouBing · GitHub 数据</text>',
    f'<text x="{W - 30}" y="40" text-anchor="end" font-family="{FONT}" font-size="10" fill="#565f89">generated from GitHub API</text>',
]

tiles = [("公开仓库", public_repos), ("获星数", stars), ("语言种类", len(lang_data)), ("加入时间", joined)]
pos = [(30, 70), (195, 70), (30, 172), (195, 172)]
for (label, value), (x, y) in zip(tiles, pos):
    parts += [
        f'<rect x="{x}" y="{y}" width="150" height="82" rx="8" fill="{PANEL}"/>',
        f'<text x="{x + 75}" y="{y + 32}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{MUTED}">{label}</text>',
        f'<text x="{x + 75}" y="{y + 65}" text-anchor="middle" font-family="{FONT}" font-size="{"26" if label == "加入时间" else "30"}" font-weight="bold" fill="{BLUE}">{value}</text>',
    ]

parts.append(f'<text x="400" y="92" font-family="{FONT}" font-size="14" fill="{MUTED}">语言分布（按代码量）</text>')
bar_x, bar_w = 545, 235
row_y = 122
for i, (name, pct) in enumerate(lang_data):
    color = LANG_COLORS.get(name, "#565f89")
    y = row_y + i * 38
    parts += [
        f'<text x="400" y="{y + 10}" font-family="{FONT}" font-size="13" fill="{TXT}">{name}</text>',
        f'<rect x="{bar_x}" y="{y}" width="{bar_w}" height="10" rx="5" fill="{PANEL}"/>',
        f'<rect x="{bar_x}" y="{y}" width="{max(bar_w * pct / 100, 6)}" height="10" rx="5" fill="{color}"/>',
        f'<text x="{bar_x + bar_w + 12}" y="{y + 10}" font-family="{FONT}" font-size="12" fill="{MUTED}">{pct:.1f}%</text>',
    ]

parts.append("</svg>")

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "assets", "github-stats.svg")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print("langs:", [(n, f"{p:.1f}%") for n, p in lang_data])
print("saved:", os.path.normpath(out))
