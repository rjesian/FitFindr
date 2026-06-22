"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.
"""

import os
from dotenv import load_dotenv
from groq import Groq
from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Returns an empty list if nothing matches — does NOT raise an exception.
    Size matching is exact (case-insensitive). "M" does NOT match "S/M".
    """
    listings = load_listings()

    # Step 1: filter by price and size
    filtered = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue
        if size is not None and item["size"].lower() != size.lower():
            continue
        filtered.append(item)

    # Step 2: score by keyword overlap with description
    keywords = description.lower().split()

    def score(item):
        text = " ".join([
            item["title"],
            item["description"],
            " ".join(item["style_tags"]),
            item["category"],
        ]).lower()
        return sum(1 for word in keywords if word in text)

    scored = [(item, score(item)) for item in filtered]

    # Step 3: drop zero-score items and sort by score descending
    matched = [(item, s) for item, s in scored if s > 0]
    matched.sort(key=lambda x: x[1], reverse=True)

    return [item for item, _ in matched]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1-2 complete outfits.
    If wardrobe is empty, returns general styling advice instead of failing.
    """
    client = _get_groq_client()
    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        prompt = f"""You are a fashion stylist. A user is considering buying this secondhand item:

Item: {new_item['title']}
Description: {new_item['description']}
Style tags: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}

They haven't shared their wardrobe yet. Give them 1-2 general outfit ideas for this item — what kinds of pieces pair well with it, what vibe it suits, and how they might wear it. Be specific and casual, not generic."""

    else:
        wardrobe_text = "\n".join(
            f"- {w['name']} ({', '.join(w['style_tags'])})"
            for w in wardrobe_items
        )
        prompt = f"""You are a fashion stylist. A user is considering buying this secondhand item:

Item: {new_item['title']}
Description: {new_item['description']}
Style tags: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}

Their current wardrobe includes:
{wardrobe_text}

Suggest 1-2 specific outfit combinations using the new item and pieces from their wardrobe. Name the actual wardrobe pieces. Be specific and casual."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Unable to generate outfit suggestion at this time. (Error: {str(e)})"


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    If outfit is empty, returns an error string instead of calling the LLM.
    """
    if not outfit or not outfit.strip():
        return "Unable to generate fit card — outfit description was empty."

    client = _get_groq_client()

    prompt = f"""Write a 2-4 sentence Instagram caption for this thrifted outfit.

Thrifted item: {new_item['title']}
Price: ${new_item['price']}
Platform: {new_item['platform']}
Outfit: {outfit}

Rules:
- Sound like a real person posting their OOTD, not a product description
- Mention the item name, price, and platform naturally (once each)
- Capture the vibe in specific terms
- Keep it casual and authentic
- No hashtags"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=1.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Unable to generate fit card at this time. (Error: {str(e)})"