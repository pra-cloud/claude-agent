"""
Daily Tech News Bot - OpenAI version
Uses OpenAI GPT-4o-mini with web search (very cheap ~$0.001 per run)
Sends digest to Telegram

Install: pip install openai requests
Secrets needed in GitHub:
  OPENAI_API_KEY
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import os
import json
import requests
from datetime import datetime
from openai import OpenAI

OPENAI_API_KEY    = os.environ["OPENAI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

TOPICS = ["DevOps & CI/CD", "AWS Cloud", "AI & LLM"]

client = OpenAI(api_key=OPENAI_API_KEY)


def fetch_news_with_openai() -> list[dict]:
    """Ask GPT-4o-mini with web search to find today's top 5 trending tech stories."""
    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""You are a senior tech news curator. Today is {today}.
Search the web and find the TOP 5 most important and trending tech stories
from the last 48 hours across these topics: {", ".join(TOPICS)}.

Prioritize: major product launches, security incidents, significant releases,
important research breakthroughs, or industry-shaping announcements.

Return ONLY a valid JSON array, no markdown, no backticks, no extra text:
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

Include stories from multiple topics. Be specific with real headlines."""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )

    # Extract text output
    full_text = ""
    for block in response.output:
        if block.type == "message":
            for content in block.content:
                if content.type == "output_text":
                    full_text += content.text

    full_text = full_text.strip()
    start = full_text.find("[")
    end = full_text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array in response:\n{full_text[:500]}")

    return json.loads(full_text[start:end + 1])


def format_telegram_message(articles: list[dict]) -> str:
    """Format articles into a clean Telegram message."""
    today = datetime.now().strftime("%A, %B %d %Y")
    lines = [
        f"🤖 *Daily Tech Digest* — {today}",
        f"📡 Topics: DevOps · AWS · AI\n",
    ]

    topic_icons = {"devops": "⚙️", "aws": "☁️", "ai": "🧠"}

    for a in articles:
        topic = a.get("topic", "Tech")
        icon = next((v for k, v in topic_icons.items() if k in topic.lower()), "📌")

        lines.append(f"{icon} *#{a.get('rank', '')} {topic}*")
        lines.append(f"*{a.get('headline', '')}*")
        lines.append(a.get("summary", ""))
        lines.append(f"_Source: {a.get('source', 'Unknown')}_")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━")
    lines.append("_Powered by OpenAI GPT-4o-mini + Web Search_")
    return "\n".join(lines)


def send_telegram_message(text: str):
    """Send message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }, timeout=15)
    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram error: {result}")


def main():
    print(f"[{datetime.now().isoformat()}] Starting daily news fetch...")
    print("  Fetching news with OpenAI + web search...")
    articles = fetch_news_with_openai()
    print(f"  Got {len(articles)} articles.")
    message = format_telegram_message(articles)
    print("  Sending to Telegram...")
    send_telegram_message(message)
    print("  Done! Digest sent successfully.")
    print("\nPreview:\n" + "=" * 50)
    print(message)


if __name__ == "__main__":
    main()
