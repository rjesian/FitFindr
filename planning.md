# FitFindr — planning.md
---

## Tools

### Tool 1: search_listings

**What it does:**
Searches a mock secondhand clothing dataset and returns listings that match the user's description, optional size, and optional max price. It filters and ranks results based on keyword relevance and similarity scoring.

**Input parameters:**
- `description` (str): Natural language description of what the user wants (e.g. "vintage graphic tee")
- `size` (str | None): Optional size filter (e.g. "M", "W30"). If None, size is ignored
- `max_price` (float | None): Optional maximum price filter. If None, price is ignored

**What it returns:**
A list of listing dictionaries sorted by relevance (highest match first). Each listing includes:
id, title, description, category, style_tags, size, condition, price, colors, brand, platform

**What happens if it fails or returns nothing:**
If no listings match, return an empty list. The agent must immediately stop execution, set `session["error"]`, and not call any further tools.

---

### Tool 2: suggest_outfit

**What it does:**
Generates outfit suggestions using a selected listing item and the user's wardrobe. It uses an LLM to propose styling combinations and outfit ideas based on fashion compatibility.

**Input parameters:**
- `new_item` (dict): Selected listing from search results
- `wardrobe` (dict): User wardrobe containing an `"items"` list

**What it returns:**
A string containing 1–2 outfit ideas showing how to style the item using wardrobe pieces or general fashion guidance.

**What happens if it fails or returns nothing:**
If the wardrobe is empty, generate general styling advice instead of failing. If the LLM fails, return a fallback message:
"Unable to generate outfit suggestion at this time."

---

### Tool 3: create_fit_card

**What it does:**
Converts an outfit description into a short, aesthetic social media caption (OOTD-style) using an LLM.

**Input parameters:**
- `outfit` (str): Outfit suggestion text from suggest_outfit
- `new_item` (dict): Selected listing item

**What it returns:**
A 2–4 sentence caption that naturally includes:
- Item name
- Price
- Platform
- Outfit vibe description in a casual, aesthetic tone

**What happens if it fails or returns nothing:**
If outfit is empty or invalid, return an error string and do not call the LLM.

---

## Planning Loop

The agent runs a strict sequential pipeline:

1. Parse user query into structured fields:
   - description
   - size (optional)
   - max_price (optional)

2. Call:
   `search_listings(description, size, max_price)`

3. If results are empty:
   - Set `session["error"] = "No matching listings found. Try adjusting size or price constraints."
   - Stop execution immediately.

4. Otherwise:
   - Select top result from search output
   - Store in `session["selected_item"]`

5. Call:
   `suggest_outfit(selected_item, wardrobe)`
   - Store result in `session["outfit_suggestion"]`

6. Call:
   `create_fit_card(outfit, selected_item)`
   - Store result in `session["fit_card"]`

7. Return full session object

This is a deterministic, state-driven pipeline where each step depends on the previous one.

---

## State Management

The agent uses a single session dictionary that persists across all tool calls.

It stores:
- `query`: original user input
- `parsed`: extracted description, size, max_price
- `search_results`: list of matching listings
- `selected_item`: top-ranked listing
- `outfit_suggestion`: output from suggest_outfit
- `fit_card`: output from create_fit_card
- `error`: error message if pipeline fails early

Each tool reads from and writes to this shared state object, ensuring a linear flow of information without global variables.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match query | Set `session["error"]` and stop execution |
| suggest_outfit | Wardrobe is empty | Generate general styling advice using LLM |
| create_fit_card | Outfit missing or invalid | Return error string and stop LLM call |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```text
User Query
    ↓
Parse Query
    ↓
search_listings()
    ↓
If no results → session["error"] → STOP
    ↓
Select Top Item
    ↓
suggest_outfit()
    ↓
create_fit_card()
    ↓
Return Session
```

---

## AI Tool Plan

### Milestone 3 — Individual tool implementations:

I will use ChatGPT (or Groq API) to help implement each tool function based on the specifications in this planning document. I will provide:

- tool input/output specs  
- dataset structure  
- example listings and wardrobe  

I will validate correctness by testing:

- normal query (vintage tee under $30)  
- size-filtered query  
- no-match edge case  

---

### Milestone 4 — Planning loop and state management:

I will use ChatGPT to verify that my `agent.py` logic matches this planning document exactly. I will manually trace session state updates step-by-step and ensure each tool is called in correct order.

---

## A Complete Interaction (Step by Step)

**Example user query:**
"I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers."

---

### Step 1:

Call `search_listings`

**Input:**
- description: "vintage graphic tee"
- size: None
- max_price: 30

**Output:**
Returns ranked list of matching graphic tees.  
Top match:
"Graphic Tee — 2003 Tour Bootleg Style"

---

### Step 2:

Select top item:
"Graphic Tee — 2003 Tour Bootleg Style"

Call `suggest_outfit(selected_item, wardrobe)`

**Output:**
Suggests pairing with baggy jeans, sneakers, and layered streetwear pieces.

---

### Step 3:

Call `create_fit_card(outfit, selected_item)`

**Output:**
Returns short OOTD caption mentioning:
- item name  
- price  
- platform  
- outfit aesthetic  

---

### Final output to user:

The user sees:

- Top listing (title, price, description)
- Outfit suggestion
- Fit card caption (social media style post)
