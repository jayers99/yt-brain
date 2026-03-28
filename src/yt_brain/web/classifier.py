"""Keyword-based genre classifier for YouTube videos."""

from __future__ import annotations

import re
from collections import Counter


RULES: list[tuple[str, list[str]]] = [
    ("AI/ML & LLMs", [
        r"\bai\b", r"\bgpt", r"\bclaude\b", r"\bllm", r"\banthropic\b", r"\bopenai\b",
        r"\bgemini\b", r"\bmachine learn", r"\bdeep learn", r"\bneural", r"\btransformer",
        r"\bagent[s]?\b", r"\bprompt", r"\bchatbot", r"\bcopilot", r"\bsora\b",
        r"\brag\b", r"\bembedding", r"\bfine.?tun", r"\binference", r"\bmcp\b",
        r"\bcursor\b", r"\bvibe.?cod", r"\bagentic", r"\bwindsurf", r"\breplit\b",
    ]),
    ("Programming & Dev Tools", [
        r"\bpython\b", r"\brust\b", r"\btypescript\b", r"\bjavascript\b", r"\breact\b",
        r"\bgit\b", r"\bdocker\b", r"\bkubernetes\b", r"\baws\b", r"\bgcp\b",
        r"\bcloud\b", r"\bdevops\b", r"\bapi\b", r"\bcode\b(?!.*\bclaud)",
        r"\bvs\s?code\b", r"\bterminal\b", r"\bcli\b", r"\blinux\b", r"\bvim\b",
        r"\bnext\.?js\b", r"\bnode\b", r"\bdatabase\b", r"\bsql\b", r"\bsupabase\b",
        r"\bframework\b", r"\bopen.?source\b",
    ]),
    ("Tech News & Industry", [
        r"\bapple\b", r"\bgoogle\b(?!.*\bai\b)", r"\bmicrosoft\b",
        r"\bstartup", r"\btech\s?(bro|compan|industr|layoff|news)",
        r"\bsilicon valley\b", r"\bsaas\b", r"\bnvidia\b", r"\bchip[s]?\b",
        r"\bsemiconductor",
    ]),
    ("Science & Education", [
        r"\bscien", r"\bphysic", r"\bchemis", r"\bbiolog", r"\bmath",
        r"\buniverse\b", r"\bquantum\b", r"\bevolution\b", r"\bbrain\b",
        r"\bneurosci", r"\bpsycholog", r"\bresearch\b", r"\bexperim",
        r"\bhow\s.*work", r"\bexplain",
    ]),
    ("History & Documentary", [
        r"\bhistor", r"\bwar\b", r"\bww[12i]\b", r"\bancient\b", r"\bempire\b",
        r"\bcentury\b", r"\bheist\b", r"\btrue\s?(story|crime)", r"\bdocumentar",
        r"\binvestigat", r"\bmystery\b", r"\bunsolved\b",
    ]),
    ("Philosophy & Self-Improvement", [
        r"\bphilosoph", r"\bstoic", r"\bmeditat", r"\bmindful", r"\bproductiv",
        r"\bhabit", r"\bmotivat", r"\bself[- ]", r"\blife\s?(lesson|hack|chang)",
        r"\bwisdom\b", r"\bmindset\b", r"\breali[zs]ation", r"\bpurpose\b",
    ]),
    ("Film, TV & Pop Culture", [
        r"\bmovie", r"\bfilm\b", r"\bcinema", r"\btrailer\b", r"\breview\b",
        r"\bscene\b", r"\bmarvel\b", r"\bstar\s?wars\b", r"\bdune\b",
        r"\bnetflix\b", r"\bseries\b", r"\bseason\b", r"\bepisode\b",
        r"\batreides\b", r"\bharkonnen\b",
    ]),
    ("Music", [
        r"\bmusic\b", r"\bsong\b", r"\balbum\b", r"\bconcert\b",
        r"\bguitar\b", r"\bpiano\b", r"\blyric", r"\bremix\b",
        r"\bofficial\s?(video|audio)", r"\bfeat\.?\b",
    ]),
    ("Gaming", [
        r"\bgam(e|ing|er)\b", r"\bplaystation\b", r"\bxbox\b", r"\bnintendo\b",
        r"\bgameplay\b", r"\bwalkthrough\b", r"\bspeedrun\b",
    ]),
    ("Finance & Business", [
        r"\bfinance\b", r"\binvest", r"\bstock", r"\bcrypto", r"\bbitcoin\b",
        r"\bmoney\b", r"\bwealth\b", r"\bretir", r"\bbudget\b",
        r"\beconom", r"\binflation\b", r"\bmarket\b",
    ]),
    ("Design & Creative", [
        r"\bdesign\b", r"\bui\b", r"\bux\b", r"\bfigma\b", r"\billustrat",
        r"\bcreativ", r"\bart\b", r"\banimation\b", r"\b3d\b", r"\bblender\b",
    ]),
    ("Food & Cooking", [
        r"\bcook", r"\brecipe\b", r"\bfood\b", r"\bchef\b", r"\brestaurant\b",
        r"\bkitchen\b", r"\bwine\b", r"\bcoffee\b", r"\bwhisk[e]?y\b",
    ]),
    ("Fitness & Health", [
        r"\bworkout\b", r"\bfitness\b", r"\bgym\b", r"\bexercis", r"\bdiet\b",
        r"\bnutrition\b", r"\bhealth\b", r"\byoga\b",
    ]),
    ("Politics & Current Events", [
        r"\bpoliti", r"\belection\b", r"\btrump\b", r"\bbiden\b",
        r"\bgovern", r"\bgeopoliti", r"\bsanction",
    ]),
    ("DIY & How-To", [
        r"\bdiy\b", r"\bhow\s?to\b", r"\btutorial\b", r"\bbuild",
        r"\bcraft\b", r"\brepair\b", r"\binstall\b", r"\bwoodwork",
    ]),
]


def classify_genre(title: str) -> str:
    t = title.lower()
    for genre, patterns in RULES:
        for p in patterns:
            if re.search(p, t):
                return genre
    return "Other"


def classify_videos(videos: list[dict]) -> list[dict]:
    for v in videos:
        v["genre"] = classify_genre(v.get("title", ""))
    return videos


def genre_stats(videos: list[dict]) -> list[dict]:
    counts = Counter(v.get("genre", "Other") for v in videos)
    total = len(videos)
    stats = []
    for genre, count in counts.most_common():
        stats.append({
            "genre": genre,
            "count": count,
            "pct": round(count / total * 100, 1) if total else 0,
        })
    return stats
