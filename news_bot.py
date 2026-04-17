"""
Daily Tech News Bot - Enhanced Version
Uses OpenAI GPT-4o-mini with web search
Sends rich digest to Telegram with source links, productivity tips, and trending tools

Install: pip install openai requests
GitHub Secrets needed:
  OPENAI_API_KEY
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import os
import json
import requests
from datetime import datetime
from openai import OpenAI

OPENAI_API_KEY     = os.environ["OPENAI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

client = OpenAI(api_key=OPENAI_API_KEY)


# ─────────────────────────────────────────────
# SECTION 1 — Top Tech News (5 stories)
# ─────────────────────────────────────────────
def fetch_top_news() -> list[dict]:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""You are a senior tech news curator. Today is {today}.
Search the web and find the TOP 5 most important and trending tech stories
from the last 48 hours across: DevOps & CI/CD, AWS Cloud, AI & LLM, Platform Engineering, SRE/Observability.

Prioritize: major product launches, security patches, breaking changes, important releases, industry shifts.

Return ONLY a valid JSON array, no markdown, no backticks:
[
  {{
    "rank": 1,
    "topic": "DevOps & CI/CD",
    "headline": "Concise impactful headline",
    "summary": "2 sentences. What happened and why engineers should care.",
    "source": "Publication or blog name",
    "url": "https://actual-article-url.com",
    "emoji": "relevant emoji"
  }}
]
Use real URLs to real articles published in the last 48 hours. Include diverse topics."""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )
    return _parse_json_response(response)


# ─────────────────────────────────────────────
# SECTION 2 — Trending AI Tools for DevOps
# ─────────────────────────────────────────────
def fetch_ai_devops_tools() -> list[dict]:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. Search the web for the TOP 3 trending AI-powered tools
for DevOps engineers right now — things like AI coding assistants, AI for infrastructure,
AIOps, AI-powered monitoring, AI for IaC, AI for security, LLM-based CLI tools, etc.

Focus on tools that are newly released, recently updated, or gaining traction this week.

Return ONLY a valid JSON array, no markdown, no backticks:
[
  {{
    "name": "Tool name",
    "category": "e.g. AI Coding / AIOps / IaC / Security",
    "what_it_does": "1 sentence description",
    "why_useful": "1 sentence on why DevOps engineers should try it",
    "url": "https://tool-website-or-article.com",
    "emoji": "relevant emoji"
  }}
]"""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )
    return _parse_json_response(response)


# ─────────────────────────────────────────────
# SECTION 3 — What's Trending in DevOps
# ─────────────────────────────────────────────
def fetch_devops_trends() -> list[dict]:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. Search the web for the TOP 3 hottest trends,
discussions, or debates in the DevOps/Platform Engineering/SRE community right now.

This could be: a new methodology gaining traction, a hot Reddit/HN thread,
a controversial opinion piece, a new best practice, an emerging pattern like
platform engineering, GitOps, FinOps, chaos engineering, etc.

Return ONLY a valid JSON array, no markdown, no backticks:
[
  {{
    "trend": "Trend name or topic",
    "summary": "2 sentences. What is it and why is the community excited or divided.",
    "source": "Where this is being discussed",
    "url": "https://article-or-discussion-url.com",
    "emoji": "relevant emoji"
  }}
]"""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )
    return _parse_json_response(response)


# ─────────────────────────────────────────────
# SECTION 4 — Daily Productivity Tip
# ─────────────────────────────────────────────
def fetch_productivity_tip() -> dict:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. Give ONE highly practical productivity tip for a DevOps/Cloud engineer.
It should be a specific command, workflow trick, tool shortcut, or lesser-known feature
that saves real time. Rotate between: shell/terminal tricks, kubectl tips, AWS CLI tricks,
git tricks, Docker tips, monitoring shortcuts, VS Code tricks, etc.

Return ONLY a valid JSON object, no markdown, no backticks:
{{
  "tip_title": "Short catchy title",
  "tip": "The actual tip with example command or steps if applicable",
  "category": "e.g. Shell / Kubernetes / AWS CLI / Git / Docker",
  "url": "https://optional-reference-link.com"
}}"""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )
    text = _extract_text(response).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {"tip_title": "Tip of the day", "tip": text[:300], "category": "General", "url": ""}
    return json.loads(text[start:end + 1])


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _extract_text(response) -> str:
    full_text = ""
    for block in response.output:
        if block.type == "message":
            for content in block.content:
                if content.type == "output_text":
                    full_text += content.text
    return full_text


def _parse_json_response(response) -> list[dict]:
    text = _extract_text(response).strip()
    text = text.replace("```json", "").replace("```", "")
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        print(f"  Warning: no JSON array found in response: {text[:200]}")
        return []
    return json.loads(text[start:end + 1])


def escape_md(text: str) -> str:
    """Escape special chars for Telegram MarkdownV2."""
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


# ─────────────────────────────────────────────
# Format full Telegram message
# ─────────────────────────────────────────────
def format_message(news, tools, trends, tip) -> str:
    today = datetime.now().strftime("%A, %B %d %Y")
    lines = []

    # Header
    lines += [
        f"🚀 *Daily DevOps & AI Digest*",
        f"📅 {today}",
        "",
    ]

    # Section 1 — Top News
    lines += ["━━━━━━━━━━━━━━━━━━━━━━", "📰 *TOP TECH NEWS*", ""]
    for a in news:
        emoji = a.get("emoji", "📌")
        topic = a.get("topic", "Tech")
        headline = a.get("headline", "")
        summary = a.get("summary", "")
        source = a.get("source", "")
        url = a.get("url", "")
        lines.append(f"{emoji} *\\#{a.get('rank','')} {escape_md(topic)}*")
        lines.append(f"*{escape_md(headline)}*")
        lines.append(escape_md(summary))
        if url:
            lines.append(f"🔗 [Read more]({url}) — _{escape_md(source)}_")
        else:
            lines.append(f"_{escape_md(source)}_")
        lines.append("")

    # Section 2 — AI Tools for DevOps
    lines += ["━━━━━━━━━━━━━━━━━━━━━━", "🤖 *TRENDING AI TOOLS FOR DEVOPS*", ""]
    for t in tools:
        emoji = t.get("emoji", "🛠")
        name = t.get("name", "")
        category = t.get("category", "")
        what = t.get("what_it_does", "")
        why = t.get("why_useful", "")
        url = t.get("url", "")
        lines.append(f"{emoji} *{escape_md(name)}* \\| _{escape_md(category)}_")
        lines.append(escape_md(what))
        lines.append(f"💡 {escape_md(why)}")
        if url:
            lines.append(f"🔗 [Try it]({url})")
        lines.append("")

    # Section 3 — DevOps Trends
    lines += ["━━━━━━━━━━━━━━━━━━━━━━", "📈 *WHAT'S TRENDING IN DEVOPS*", ""]
    for tr in trends:
        emoji = tr.get("emoji", "🔥")
        trend = tr.get("trend", "")
        summary = tr.get("summary", "")
        source = tr.get("source", "")
        url = tr.get("url", "")
        lines.append(f"{emoji} *{escape_md(trend)}*")
        lines.append(escape_md(summary))
        if url:
            lines.append(f"🔗 [Read more]({url}) — _{escape_md(source)}_")
        lines.append("")

    # Section 4 — Productivity Tip
    lines += ["━━━━━━━━━━━━━━━━━━━━━━", "⚡ *PRODUCTIVITY TIP OF THE DAY*", ""]
    tip_title = tip.get("tip_title", "")
    tip_text = tip.get("tip", "")
    tip_cat = tip.get("category", "")
    tip_url = tip.get("url", "")
    lines.append(f"*{escape_md(tip_title)}* \\| _{escape_md(tip_cat)}_")
    lines.append(escape_md(tip_text))
    if tip_url:
        lines.append(f"🔗 [Reference]({tip_url})")
    lines.append("")

    # Footer
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "_Powered by OpenAI GPT\\-4o\\-mini \\+ Web Search_",
        "_Delivered daily at 8:00 AM IST_ 🇮🇳",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Send to Telegram
# ─────────────────────────────────────────────
def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False,
    }, timeout=15)
    result = resp.json()
    if not result.get("ok"):
        # Fallback: send as plain text if markdown fails
        print(f"  MarkdownV2 failed: {result.get('description')} — retrying as plain text")
        plain = text.replace("\\", "").replace("*", "").replace("_", "").replace("`", "")
        resp2 = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": plain,
            "disable_web_page_preview": False,
        }, timeout=15)
        result2 = resp2.json()
        if not result2.get("ok"):
            raise RuntimeError(f"Telegram error: {result2}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print(f"[{datetime.now().isoformat()}] Starting enhanced news bot...")

    print("  [1/4] Fetching top tech news...")
    news = fetch_top_news()
    print(f"        Got {len(news)} stories")

    print("  [2/4] Fetching trending AI tools for DevOps...")
    tools = fetch_ai_devops_tools()
    print(f"        Got {len(tools)} tools")

    print("  [3/4] Fetching DevOps trends...")
    trends = fetch_devops_trends()
    print(f"        Got {len(trends)} trends")

    print("  [4/4] Fetching productivity tip...")
    tip = fetch_productivity_tip()
    print(f"        Got tip: {tip.get('tip_title', '')}")

    print("  Formatting and sending to Telegram...")
    message = format_message(news, tools, trends, tip)
    send_telegram(message)

    print("  ✅ Done! Full digest sent successfully.")
    print(f"\n{'='*60}\nPREVIEW:\n{'='*60}")
    print(message.replace("\\", ""))


if __name__ == "__main__":
    main()
