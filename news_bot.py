"""
Daily Tech News Bot
Fetches top 5 trending news for DevOps, AWS Cloud, and AI using Claude AI,
then sends a formatted digest to your Telegram chat.

Requirements:
  pip install anthropic requests

Environment variables needed:
  ANTHROPIC_API_KEY  - from https://console.anthropic.com
  TELEGRAM_BOT_TOKEN - from @BotFather on Telegram
  TELEGRAM_CHAT_ID   - your personal chat ID (run get_chat_id.py once to find it)
"""

import os
import json
import requests
import anthropic
from datetime import datetime


ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TOPICS = ["DevOps & CI/CD", "AWS Cloud", "AI & LLM"]


def fetch_news_with_claude() -> list[dict]:
    """Ask Claude (with web search) to find today's top 5 trending tech stories."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""You are a senior tech news curator. Today is {today}.
Search the web right now and find the TOP 5 most important and trending tech stories
from the last 48 hours across these topics: {", ".join(TOPICS)}.

Prioritize: major product launches, security incidents, significant releases,
important research breakthroughs, or industry-shaping announcements.

Return ONLY a valid JSON array with no markdown, no backticks, no extra text:
[
  {{
    "rank": 1,
    "topic": "DevOps & CI/CD",
    "headline": "Short impactful headline under 12 words",
    "summary": "2 sentence summary. Why it matters for engineers.",
    "source": "Publication name",
    "emoji": "relevant emoji"
  }}
]

Include stories from multiple topics if possible. Be specific with real headlines."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract text from response (Claude may have used web search tool first)
    full_text = ""
    for block in response.content:
        if block.type == "text":
            full_text += block.text

    # Parse JSON from response
    full_text = full_text.strip()
    start = full_text.find("[")
    end = full_text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in Claude response:\n{full_text[:500]}")

    articles = json.loads(full_text[start:end + 1])
    return articles


def format_telegram_message(articles: list[dict]) -> str:
    """Format articles into a clean Telegram message with Markdown."""
    today = datetime.now().strftime("%A, %B %d %Y")
    lines = [
        f"🤖 *Daily Tech Digest* — {today}",
        f"📡 Topics: DevOps · AWS · AI\n",
    ]

    topic_icons = {
        "devops": "⚙️",
        "aws": "☁️",
        "ai": "🧠",
    }

    for a in articles:
        topic = a.get("topic", "Tech")
        emoji = a.get("emoji", "📌")

        # Pick icon based on topic keyword
        icon = "📌"
        for key, val in topic_icons.items():
            if key in topic.lower():
                icon = val
                break

        lines.append(f"{icon} *#{a.get('rank', '')} {topic}*")
        lines.append(f"*{a.get('headline', '')}*")
        lines.append(a.get("summary", ""))
        lines.append(f"_Source: {a.get('source', 'Unknown')}_")
        lines.append("")  # blank line between stories

    lines.append("━━━━━━━━━━━━━━━")
    lines.append("_Powered by Claude AI + Web Search_")

    return "\n".join(lines)


def send_telegram_message(text: str) -> bool:
    """Send a message to Telegram using the Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    response = requests.post(url, json=payload, timeout=15)
    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")

    return True


def main():
    print(f"[{datetime.now().isoformat()}] Starting daily news fetch...")

    print("  Fetching news with Claude AI + web search...")
    articles = fetch_news_with_claude()
    print(f"  Got {len(articles)} articles.")

    print("  Formatting Telegram message...")
    message = format_telegram_message(articles)

    print("  Sending to Telegram...")
    send_telegram_message(message)

    print("  Done! Digest sent successfully.")
    print("\nPreview:\n" + "=" * 50)
    print(message)


if __name__ == "__main__":
    main()
