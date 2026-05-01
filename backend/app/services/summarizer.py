import json
from app.config import settings
from app.database import SessionLocal
from app.models.article import Article

_VALID_CATEGORIES = {
    "tech", "science", "health", "sports", "politics",
    "business", "entertainment", "environment", "gaming", "crypto", "general",
}

_PROMPT = """\
You are Verax's AI analyst. Mission: less noise, more truth.
Analyze the article. Reply ONLY with valid JSON — no extra text.

Title: {title}
Text:  {text}

Return exactly:
{{
  "summary":           "3 clear sentences — who, what, why it matters",
  "category":          "pick exactly ONE word from: tech, science, health, sports, politics, business, entertainment, environment, gaming, crypto, general",
  "bias":              "pick exactly ONE from: left, center-left, center, center-right, right, neutral",
  "bias_confidence":   80,
  "bias_reason":       "one sentence",
  "tags":              ["tag1", "tag2", "tag3"],
  "read_time_seconds": 120
}}"""


def _call_ai(title: str, text: str) -> dict:
    prompt = _PROMPT.format(title=title, text=text)

    if settings.ai_provider == "groq":
        from groq import Groq
        client = Groq(api_key=settings.groq_api_key)
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return json.loads(res.choices[0].message.content)

    if settings.ai_provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(prompt)
        text_out = res.text.strip()
        if text_out.startswith("```"):
            text_out = text_out.split("```")[1]
            if text_out.startswith("json"):
                text_out = text_out[4:]
        return json.loads(text_out)

    import ollama
    res = ollama.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        format="json",
    )
    return json.loads(res["message"]["content"])


def summarize_pending() -> None:
    db = SessionLocal()
    try:
        pending = (
            db.query(Article)
            .filter(Article.summarized == False)
            .limit(settings.batch_summarize)
            .all()
        )
        for article in pending:
            if not article.text:
                article.summarized = True
                db.commit()
                continue
            try:
                data = _call_ai(article.title, article.text[:2000])
                article.summary         = data.get("summary")
                raw_cat = str(data.get("category", "")).split("|")[0].split(",")[0].strip().lower()
                article.category        = raw_cat if raw_cat in _VALID_CATEGORIES else article.category
                article.bias            = data.get("bias", "neutral")
                article.bias_confidence = int(data.get("bias_confidence", 0))
                article.bias_reason     = data.get("bias_reason")
                article.tags            = ",".join(data.get("tags", []))
                article.read_time       = int(data.get("read_time_seconds", 60))
                article.summarized      = True
                db.commit()
            except Exception:
                db.rollback()
    finally:
        db.close()
