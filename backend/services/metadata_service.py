import json
import re

from flask import current_app
from openai import OpenAI


def fallback_metadata(context):
    clean = re.sub(r"[^\w\s-]", "", context).strip() or "New video"
    words = clean.split()
    title = " ".join(words[:12])[:100]
    tags = list(dict.fromkeys(word.lower() for word in words if len(word) > 3))[:15]
    return {"title": title, "title_alternatives": [], "description": context[:5000],
            "summary": " ".join(words[:40]), "tags": tags, "hashtags": [f"#{tag.replace(' ', '')}" for tag in tags[:5]],
            "seo_keywords": tags, "category_id": "22", "playlist_suggestion": "",
            "chapters": [], "pinned_comment": "What did you find most useful?",
            "social_post": title, "source": "fallback"}


def generate_metadata(context, prompt_override=None):
    if not current_app.config.get("OPENAI_API_KEY"):
        return fallback_metadata(context)
    prompt = prompt_override or """Create YouTube metadata from the supplied content. Return strict JSON with keys title,
title_alternatives, description, summary, tags, hashtags, seo_keywords, category_id, playlist_suggestion,
chapters (array), pinned_comment, social_post. Title <=100 chars; description <=5000 chars; total tags <=500 chars."""
    response = OpenAI(api_key=current_app.config["OPENAI_API_KEY"]).chat.completions.create(
        model=current_app.config["OPENAI_MODEL"], response_format={"type": "json_object"},
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": context[:50000]}])
    result = json.loads(response.choices[0].message.content)
    result["title"] = str(result.get("title", ""))[:100]
    result["description"] = str(result.get("description", ""))[:5000]
    result["tags"] = [str(v)[:100] for v in result.get("tags", [])]
    while len(",".join(result["tags"])) > 500:
        result["tags"].pop()
    result["source"] = "ai"
    return result
