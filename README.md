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

### `search_listings(description, size, max_price)`
**Purpose:** Searches the mock secondhand listings dataset and returns items matching the user's description, optional size, and optional price ceiling.

**Inputs:**
- `description` (str): Natural language keywords describing the item (e.g. "vintage graphic tee")
- `size` (str | None): Exact size string to filter by. Case-insensitive, exact match only — "M" does NOT match "S/M". If None, size is not filtered.
- `max_price` (float | None): Maximum price inclusive. If None, price is not filtered.

**Returns:** A list of listing dicts sorted by keyword relevance score. Each dict contains: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand`, `platform`. Returns an empty list if nothing matches.

---

### `suggest_outfit(new_item, wardrobe)`
**Purpose:** Uses the Groq LLM to generate 1–2 outfit ideas combining the new thrifted item with pieces from the user's wardrobe.

**Inputs:**
- `new_item` (dict): A listing dict returned by `search_listings`
- `wardrobe` (dict): A wardrobe dict with an `"items"` key containing a list of wardrobe item dicts. May be empty.

**Returns:** A non-empty string with outfit suggestions. If the wardrobe is empty, returns general styling advice instead of failing.

---

### `create_fit_card(outfit, new_item)`
**Purpose:** Uses the Groq LLM to generate a short, casual Instagram-style caption for the outfit.

**Inputs:**
- `outfit` (str): Outfit suggestion string from `suggest_outfit`
- `new_item` (dict): The listing dict for the thrifted item

**Returns:** A 2–4 sentence caption string mentioning the item name, price, and platform naturally. If `outfit` is empty, returns an error string without calling the LLM.

---

## Planning Loop

The agent runs a conditional sequential pipeline in `agent.py`:

1. Parse the user query with regex to extract `description`, `size` (looks for "size X"), and `max_price` (looks for "under $X")
2. Call `search_listings(description, size, max_price)`
3. **Branch:** if results are empty → set `session["error"]` and return early. Do NOT call `suggest_outfit` with empty input.
4. If results exist → set `session["selected_item"] = results[0]`
5. Call `suggest_outfit(selected_item, wardrobe)` → store in `session["outfit_suggestion"]`
6. Call `create_fit_card(outfit_suggestion, selected_item)` → store in `session["fit_card"]`
7. Return session

The agent behaves differently based on what `search_listings` returns — it does not call all three tools unconditionally.

---

## State Management

All state is stored in a single session dict initialized in `_new_session()` in `agent.py`. It tracks:

- `query`: original user input
- `parsed`: extracted description, size, max_price
- `search_results`: full list of matching listings
- `selected_item`: top result, passed directly into `suggest_outfit`
- `wardrobe`: user's wardrobe dict
- `outfit_suggestion`: string from `suggest_outfit`, passed directly into `create_fit_card`
- `fit_card`: final caption string
- `error`: set if the pipeline terminates early

No global variables are used. Each tool reads its inputs from the session and writes its output back, so information flows between tools without re-prompting the user.

---

## AI Usage

**Instance 1 — `tools.py` implementation:**
I gave Claude the Tool 1, 2, and 3 spec blocks from `planning.md` (inputs, return values, failure modes) and asked it to implement all three functions. Before using the output I checked: does `search_listings` filter by all three parameters? Does it handle empty results without crashing? Does `suggest_outfit` branch on empty wardrobe? Does `create_fit_card` guard against empty outfit string? I overrode the starter docstring's suggestion of fuzzy size matching and kept exact matching as specced, since the starter's behavior conflicted with my documented design decision.

**Instance 2 — `agent.py` planning loop:**
I gave Claude the Planning Loop and State Management sections from `planning.md` plus the architecture diagram and asked it to implement `run_agent()`. Before using the output I verified: does it branch on empty search results before calling `suggest_outfit`? Does it store values in the session dict at each step? Does it avoid calling all three tools unconditionally? The generated code matched the spec on all three checks — no overrides needed beyond confirming the regex parsing handled the example queries correctly.

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

**One way planning.md helped during implementation:**
Writing the conditional logic for the planning loop in plain English before touching `agent.py` made the implementation straightforward. The spec described exactly what to check (`if not results`) and what to do in each branch, so the code in `run_agent()` mapped almost directly to what was written in `planning.md`. Without that, it would have been easy to accidentally call `suggest_outfit` with empty input and get a confusing error instead of a clean failure message.

**One divergence from your spec, and why:**
The original spec described size matching as exact string equality with no fuzzy matching. The starter repo's docstring suggested case-insensitive partial matching where "M" would match "S/M". I kept exact matching but added case-insensitivity so that "m" and "M" both work, while still rejecting "S/M" as a non-match. This was a deliberate override of the starter's suggested behavior — exact matching is more predictable and makes the no-results error path meaningful rather than silently returning wrong results.

---
