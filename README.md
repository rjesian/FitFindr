# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

---

## Interaction Walkthrough

**User query:** "vintage graphic tee under $30"

**Step 1 — Tool called:**
- Tool: `search_listings`
- Input: `description="vintage graphic tee"`, `size=None`, `max_price=30.0`
- Why this tool: Always called first to find matching listings before anything else can happen
- Output: List of listings sorted by relevance. Top result: "Y2K Baby Tee — Butterfly Print", $18, depop

**Step 2 — Tool called:**
- Tool: `suggest_outfit`
- Input: `new_item=<Y2K Baby Tee dict>`, `wardrobe=<example wardrobe>`
- Why this tool: Called only because Step 1 returned results — uses the top listing and the user's wardrobe to generate outfit ideas
- Output: "Pair the Y2K Baby Tee with your baggy straight-leg jeans and chunky white sneakers..."

**Step 3 — Tool called:**
- Tool: `create_fit_card`
- Input: `outfit=<suggestion from Step 2>`, `new_item=<Y2K Baby Tee dict>`
- Why this tool: Called last, after an outfit suggestion exists — converts it into a shareable caption
- Output: "I'm obsessed with this Y2K Baby Tee I scored on depop for $18..."

**Final output to user:** All three panels populate — listing details, outfit suggestion, and fit card caption.

---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the query | Sets `session["error"]` = "No matching listings found. Try a different description, remove the size filter, or increase your max price." Returns session immediately without calling further tools. |
| `suggest_outfit` | Wardrobe is empty (`wardrobe["items"]` is `[]`) | Calls LLM with a general styling prompt instead of a wardrobe-specific one. Returns general outfit advice — does not crash or return empty string. |
| `create_fit_card` | `outfit` string is empty or whitespace | Returns "Unable to generate fit card — outfit description was empty." without calling the LLM. |

**Example from testing:**
```bash
python3 -c "
from tools import search_listings, create_fit_card
results = search_listings('vintage graphic tee', size=None, max_price=50)
print(create_fit_card('', results[0]))
"
# Output: Unable to generate fit card — outfit description was empty.
```
---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->


Writing the conditional logic for the planning loop in plain English before touching `agent.py` made the implementation straightforward. The spec described exactly what to check (`if not results`) and what to do in each branch, so the code in `run_agent()` mapped almost directly to what was written in `planning.md`. Without that, it would have been easy to accidentally call `suggest_outfit` with empty input and get a confusing error instead of a clean failure message.


The original spec described size matching as exact string equality with no fuzzy matching. The starter repo's docstring suggested case-insensitive partial matching where "M" would match "S/M". I kept exact matching but added case-insensitivity so that "m" and "M" both work, while still rejecting "S/M" as a non-match. This was a deliberate override of the starter's suggested behavior — exact matching is more predictable and makes the no-results error path meaningful rather than silently returning wrong results.

---
