"""
Daily Tech News Bot - Enhanced Version
Uses OpenAI GPT-4o-mini with web search
Sends rich digest to Telegram in multiple messages (avoids 4096 char limit)

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
# SECTION 1 — Top Tech News
# ─────────────────────────────────────────────
def fetch_top_news() -> list[dict]:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""You are a senior tech news curator. Today is {today}.
Search the web and find the TOP 5 most important trending tech stories
from the last 48 hours across: DevOps & CI/CD, AWS Cloud, AI & LLM, Platform Engineering, SRE/Observability.

Prioritize: major product launches, security patches, breaking changes, important releases.

Return ONLY a valid JSON array, no markdown, no backticks:
[
  {{
    "rank": 1,
    "topic": "DevOps & CI/CD",
    "headline": "Concise headline under 12 words",
    "summary": "Max 2 short sentences. What happened and why it matters.",
    "source": "Publication name",
    "url": "https://actual-article-url.com",
    "emoji": "relevant emoji"
  }}
]
Use real URLs. Keep summaries SHORT."""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )
    return _parse_json_list(response)


# ─────────────────────────────────────────────
# SECTION 2 — Trending AI Tools for DevOps
# ─────────────────────────────────────────────
def fetch_ai_devops_tools() -> list[dict]:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. Search the web for TOP 3 trending AI-powered tools
for DevOps engineers right now — AI coding assistants, AIOps, AI for IaC, AI monitoring, LLM CLI tools, etc.

Return ONLY a valid JSON array, no markdown, no backticks:
[
  {{
    "name": "Tool name",
    "category": "AI Coding / AIOps / IaC / Security / etc",
    "what_it_does": "One short sentence.",
    "why_useful": "One short sentence on why DevOps engineers should try it.",
    "url": "https://tool-url.com",
    "emoji": "relevant emoji"
  }}
]"""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )
    return _parse_json_list(response)


# ─────────────────────────────────────────────
# SECTION 3 — Trending in DevOps
# ─────────────────────────────────────────────
def fetch_devops_trends() -> list[dict]:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. Search the web for TOP 3 hottest trends or discussions
in the DevOps/Platform Engineering/SRE community right now.

Return ONLY a valid JSON array, no markdown, no backticks:
[
  {{
    "trend": "Trend name",
    "summary": "Max 2 short sentences on what it is and why the community cares.",
    "source": "Source name",
    "url": "https://url.com",
    "emoji": "relevant emoji"
  }}
]"""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )
    return _parse_json_list(response)


# ─────────────────────────────────────────────
# SECTION 4 — Productivity Tip
# ─────────────────────────────────────────────
def fetch_productivity_tip() -> dict:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. Give ONE practical productivity tip for a DevOps/Cloud engineer.
A specific command, workflow trick, or lesser-known feature that saves real time.
Rotate between: shell tricks, kubectl, AWS CLI, git, Docker, VS Code, monitoring shortcuts.

Return ONLY a valid JSON object, no markdown, no backticks:
{{
  "tip_title": "Short catchy title",
  "tip": "The actual tip. Keep it under 3 sentences. Include example command if applicable.",
  "category": "Shell / Kubernetes / AWS CLI / Git / Docker / etc",
  "url": "https://reference-link.com"
}}"""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )
    text = _extract_text(response).strip().replace("```json", "").replace("```", "")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return {"tip_title": "Tip of the day", "tip": text[:200], "category": "General", "url": ""}
    return json.loads(text[start:end + 1])


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _extract_text(response) -> str:
    out = ""
    for block in response.output:
        if block.type == "message":
            for content in block.content:
                if content.type == "output_text":
                    out += content.text
    return out


def _parse_json_list(response) -> list[dict]:
    text = _extract_text(response).strip().replace("```json", "").replace("```", "")
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        print(f"  Warning: no JSON found: {text[:150]}")
        return []
    return json.loads(text[start:end + 1])


def esc(text: str) -> str:
    """Escape special chars for Telegram MarkdownV2."""
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = str(text).replace(ch, f"\\{ch}")
    return text


# ─────────────────────────────────────────────
# Build separate message chunks
# ─────────────────────────────────────────────
def build_messages(news, tools, trends, tip) -> list[str]:
    today = datetime.now().strftime("%A, %B %d %Y")
    messages = []

    # ── Message 1: Header + Top News ──
    lines = [
        f"🚀 *Daily DevOps & AI Digest*",
        f"📅 {esc(today)}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📰 *TOP TECH NEWS*",
        "",
    ]
    for a in news:
        emoji  = a.get("emoji", "📌")
        rank   = a.get("rank", "")
        topic  = esc(a.get("topic", "Tech"))
        hl     = esc(a.get("headline", ""))
        summ   = esc(a.get("summary", ""))
        source = esc(a.get("source", ""))
        url    = a.get("url", "")
        lines.append(f"{emoji} *\\#{rank} {topic}*")
        lines.append(f"*{hl}*")
        lines.append(summ)
        if url:
            lines.append(f"🔗 [Read more]({url}) — _{source}_")
        else:
            lines.append(f"_{source}_")
        lines.append("")
    messages.append("\n".join(lines))

    # ── Message 2: AI Tools ──
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "🤖 *TRENDING AI TOOLS FOR DEVOPS*",
        "",
    ]
    for t in tools:
        emoji = t.get("emoji", "🛠")
        name  = esc(t.get("name", ""))
        cat   = esc(t.get("category", ""))
        what  = esc(t.get("what_it_does", ""))
        why   = esc(t.get("why_useful", ""))
        url   = t.get("url", "")
        lines.append(f"{emoji} *{name}* \\| _{cat}_")
        lines.append(what)
        lines.append(f"💡 {why}")
        if url:
            lines.append(f"🔗 [Try it]({url})")
        lines.append("")
    messages.append("\n".join(lines))

    # ── Message 3: Trends ──
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📈 *WHAT'S TRENDING IN DEVOPS*",
        "",
    ]
    for tr in trends:
        emoji  = tr.get("emoji", "🔥")
        trend  = esc(tr.get("trend", ""))
        summ   = esc(tr.get("summary", ""))
        source = esc(tr.get("source", ""))
        url    = tr.get("url", "")
        lines.append(f"{emoji} *{trend}*")
        lines.append(summ)
        if url:
            lines.append(f"🔗 [Read more]({url}) — _{source}_")
        lines.append("")
    messages.append("\n".join(lines))

    # ── Message 4: Tip + Footer ──
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "⚡ *PRODUCTIVITY TIP OF THE DAY*",
        "",
        f"*{esc(tip.get('tip_title',''))}* \\| _{esc(tip.get('category',''))}_",
        esc(tip.get("tip", "")),
    ]
    tip_url = tip.get("url", "")
    if tip_url:
        lines.append(f"🔗 [Reference]({tip_url})")
    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "_Powered by OpenAI GPT\\-4o\\-mini \\+ Web Search_",
        "_Delivered daily at 8:00 AM IST_ 🇮🇳",
    ]
    messages.append("\n".join(lines))

    return messages


# ─────────────────────────────────────────────
# Send to Telegram (with plain text fallback)
# ─────────────────────────────────────────────
def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    def post(payload):
        r = requests.post(url, json=payload, timeout=15)
        return r.json()

    result = post({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False,
    })

    if not result.get("ok"):
        print(f"  MarkdownV2 failed ({result.get('description')}) — retrying as plain text")
        plain = text
        for ch in r"\_*[]()~`>#+-=|{}.!":
            plain = plain.replace(f"\\{ch}", ch)
        plain = plain.replace("*", "").replace("_", "").replace("`", "")
        result2 = post({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": plain[:4000],
            "disable_web_page_preview": False,
        })
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

    print("  Sending 4 messages to Telegram...")
    messages = build_messages(news, tools, trends, tip)
    for i, msg in enumerate(messages, 1):
        print(f"    Sending message {i}/{len(messages)} ({len(msg)} chars)...")
        send_telegram(msg)

    print("  ✅ Done! Full digest sent successfully.")


if __name__ == "__main__":
    main()
