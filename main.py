"""Customer Feedback Analyzer."""
import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

import llm

POS = {"good", "great", "excellent", "love", "fast", "friendly", "fresh", "clean", "amazing",
       "helpful", "affordable", "nice", "perfect", "recommend", "quick", "polite"}
NEG = {"bad", "slow", "late", "rude", "expensive", "cold", "dirty", "poor", "terrible",
       "wrong", "never", "worst", "delayed", "broken", "overpriced", "stale", "waited"}
NEGATORS = {"not", "no", "never", "isn't", "wasn't", "didn't", "don't"}
THEMES = {
    "delivery": ["delivery", "deliver", "rider", "late", "delayed", "arrived", "waited"],
    "price": ["price", "expensive", "cheap", "affordable", "overpriced", "cost"],
    "quality": ["quality", "fresh", "stale", "taste", "broken", "cold", "food"],
    "staff": ["staff", "rude", "friendly", "polite", "attendant", "service"],
    "app/ordering": ["app", "website", "order", "checkout", "payment"],
}


def sentiment(text: str) -> float:
    words = re.findall(r"[a-z']+", text.lower())
    score, hits = 0, 0
    for i, w in enumerate(words):
        val = 1 if w in POS else -1 if w in NEG else 0
        if val and i > 0 and words[i - 1] in NEGATORS:
            val = -val
        if val:
            score, hits = score + val, hits + 1
    return round(score / hits, 2) if hits else 0.0


def themes_of(text: str):
    t = text.lower()
    return [k for k, words in THEMES.items() if any(w in t for w in words)]


def analyse(rows):
    agg = defaultdict(lambda: {"n": 0, "sent": 0.0, "neg_quotes": []})
    scored = []
    for r in rows:
        s = sentiment(r["comment"])
        th = themes_of(r["comment"])
        scored.append({**r, "sentiment": s, "themes": th})
        for t in th:
            agg[t]["n"] += 1
            agg[t]["sent"] += s
            if s < 0:
                agg[t]["neg_quotes"].append(r["comment"])
    summary = []
    for t, v in agg.items():
        avg = v["sent"] / v["n"]
        summary.append({"theme": t, "mentions": v["n"], "avg_sentiment": round(avg, 2),
                        "impact": round(v["n"] * max(0, -avg), 2), "quotes": v["neg_quotes"][:2]})
    summary.sort(key=lambda x: (-x["impact"], x["avg_sentiment"]))
    return scored, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="sample_feedback.csv")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.input, encoding="utf-8")))
    scored, summary = analyse(rows)
    overall = sum(s["sentiment"] for s in scored) / len(scored)
    lines = ["# Customer feedback report", "", f"Comments analysed: {len(scored)}",
             f"Overall sentiment: {overall:+.2f} (-1 to +1)", "", "## Fix first", ""]
    print(f"{len(scored)} comments, overall sentiment {overall:+.2f}\n")
    print("Theme          Mentions  Avg sent  Impact")
    for s in summary:
        print(f"{s['theme']:<14} {s['mentions']:>8}  {s['avg_sentiment']:>+8.2f}  {s['impact']:>6}")
        lines.append(f"- **{s['theme']}**: {s['mentions']} mentions, sentiment "
                     f"{s['avg_sentiment']:+.2f}" + (f' — e.g. "{s["quotes"][0]}"' if s["quotes"] else ""))
    ai = llm.complete("Summarise in 3 bullet points what this business should fix first:\n"
                      + "\n".join(lines))
    if ai:
        lines += ["", "## AI summary", "", ai]
    Path("output").mkdir(exist_ok=True)
    Path("output/feedback_report.md").write_text("\n".join(lines))
    top = summary[0]
    print(f"\nFix first: {top['theme']} -> \"{top['quotes'][0] if top['quotes'] else ''}\"")
    print("Saved output/feedback_report.md")


if __name__ == "__main__":
    main()
