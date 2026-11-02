# Empório da Música — Customer Service Agent ("Clave")

Prototype of a text-message customer service agent for **Empório da Música**, a fictional musical instrument store in Campo Grande/MS (Brazil), built for the Artefact AI Engineer technical challenge.

> Work in progress: sections are filled in as the project evolves.

## 1. Overview

**Clave** is the virtual assistant of Empório da Música. It answers customer text messages in Brazilian Portuguese with the tone the store manual asks for (section 7.1): informal but professional, "like talking to a friend who understands music".

For each message, the agent decides by itself what it needs to look up:

- **Store data** (CSV files): product search, price, availability, active promotions, payment conditions and order status.
- **Store policies** (internal manual): address and contacts, opening hours, payment methods, returns and exchanges, shipping, promotion rules, warranty and privacy.

Values with an objective rule in the manual (PIX discount, promotional price, installments, Campo Grande shipping, return and warranty periods, opening hours) are computed in Python and only written by the model, never calculated by it.

**Scope.** The store sells musical instruments only (manual 1 and 7.1). Requests for accessories are politely declined, questions unrelated to the store are not answered, and anything the agent cannot do (complaints, shipping quotes outside Campo Grande, special requests) is handed off to the human team with the official contacts.

## 2. How to run

Everything used here is free: no credit card, paid plan or expiring credits are needed.

### Requirements

- Python 3.11 or newer (developed and tested with Python 3.12 on Windows).
- A Google account, to create a free Gemini API key.

### Setup

1. Clone the repository and enter the folder:

   ```bash
   git clone https://github.com/ArnaldSouza/emporio-da-musica-agent.git
   cd emporio-da-musica-agent
   ```

2. Create and activate a virtual environment, then install the dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows (PowerShell: .\.venv\Scripts\Activate.ps1)
   source .venv/bin/activate      # Linux / macOS
   pip install -r requirements.txt
   ```

3. Create a free Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey). Creating a new project for the key is recommended, because free-tier limits are counted per project. **Do not enable billing**: the free tier is enough. At the time of writing, AI Studio showed these free limits for `gemini-3.5-flash-lite`: 15 requests per minute, 250,000 tokens per minute and 500 requests per day. Each customer message uses 2 or 3 requests.

4. Copy `.env.example` to `.env` and paste your key into `LLM_API_KEY`:

   ```bash
   cp .env.example .env           # Windows PowerShell: Copy-Item .env.example .env
   ```

   The `.env` file is listed in `.gitignore` and must never be committed.

### Run

```bash
python main.py                 # chat with Clave in the terminal
python main.py --show-tools    # also shows which tools the agent called on each turn
```

Type `sair` (or press Ctrl+C) to end the conversation.

### Tests

```bash
python -m pytest
```

The tests cover the business rules, the data and policy tools, the prompt and the conversation loop (with a fake model client). They never call the real model, so they use no API quota.

### Configuration (`.env`)

| Variable | Purpose | Default in `.env.example` |
| --- | --- | --- |
| `LLM_API_KEY` | API key of the model provider | (your key) |
| `LLM_BASE_URL` | Any OpenAI-compatible endpoint | Gemini OpenAI-compatible endpoint |
| `LLM_MODEL` | Model name | `gemini-3.5-flash-lite` |
| `REFERENCE_DATE` | Date treated as "today" by order rules (see Assumptions) | `2026-03-25` |

### Alternative: local model with Ollama (not tested)

Because the client uses the OpenAI-compatible API, a local model can be used without code changes: install [Ollama](https://ollama.com), download a model with tool-calling support, and set `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_MODEL` to the model name and `LLM_API_KEY` to any non-empty value. This path was not tested: on the author's laptop (16 GB RAM, integrated GPU, so CPU-only inference) responses would be slow, and small local models are less reliable at function calling.

## 3. Architecture

To be completed.

## 4. Technical decisions and justification

Agent approach, model and provider, interface and conversation history: to be completed.

### 4.1 Data handling

The CSV files are read with pandas and never modified on disk. All preparation happens in memory when the agent starts (`tools.py`).

- **Products:** joined with categories and with the active promotion (`is_active == 1`; if a product ever had two, the highest discount would be used). Availability is derived from status and stock, with status prevailing. Descriptions are dropped (see Assumptions), `specs` JSON is parsed, and a normalized name (lowercase, no accents) allows accent-insensitive search.
- **Orders:** joined with the customer's contact data and a readable list of items; dates are parsed and status and payment codes are translated into Portuguese.
- **Business rules:** every rule with an objective criterion in the manual (PIX discount, promotional price, installments, combined payments, Campo Grande shipping, return window, defect coverage, opening hours) is a pure function in `business_rules.py`, never computed by the LLM. Money uses `Decimal` with half-up rounding to avoid one-cent errors (R$ 599.90 with 5% off is R$ 569.91, not R$ 569.90).
- **Tests:** rules and tools are covered by unit tests in `tests/`, which run without calling the model.

### 4.2 Policy retrieval

The manual (8 pages, about 1,700 words, 10 numbered sections) is extracted with `pypdf` in layout mode, cleaned (page headers and footers removed, contacts standardized) and split into its numbered sections. A section starts only at the next expected number, so numbered steps inside a section are not taken as titles. The policy tool returns the section of a fixed topic: about the store, opening hours, payment, returns and exchanges, shipping, promotions, warranty or privacy. Sections 7 (internal service guidelines) and 10 (final provisions) are not exposed to customers; section 7 guides the system prompt.

- **Why not embeddings (vector RAG):** the document is short and already divided by topic; a vector store would add infrastructure and dependencies without better retrieval.
- **Why not the whole manual in the prompt:** simpler, but the decision of when to consult the policies, which the challenge evaluates, would become invisible, and every request would carry thousands of extra tokens.

## 5. Assumptions

The challenge asks to assume a reasonable interpretation whenever something is ambiguous. These are the interpretations used, grouped by topic.

### Dates

- The data is a snapshot of a period of the year (last order on 2026-03-22). "Today" for date-based rules is the fixed reference date **2026-03-25**, configurable through `REFERENCE_DATE` in `.env`.
- There is no actual delivery date: for `delivered` orders, `estimated_delivery` is treated as the date the customer received the product.

### Opening hours

- The manual's hours are local Campo Grande time (UTC-4). The agent checks whether the store is open using Campo Grande time and always shows both times, e.g. "09h às 18h (horário de MS) / 10h às 19h (horário de Brasília)", since customers may be in other time zones.
- The agent answers data and policy questions at any time. Outside business hours, when a request needs the human team, it says when the team will be back (manual 2 and 7.1).

### Orders and privacy

- To see an order, the customer must give the order number and the e-mail or phone registered for it (manual 9, LGPD). The agent never returns data from other orders.
- All orders in the data are treated as online purchases, so the right of withdrawal (manual 4.1) applies.

### Payments and promotions

- Installments follow manual 3.1: up to 3x with a minimum installment of R$ 50; 4x–6x, R$ 80; 7x–12x, R$ 100.
- A promotion is valid only when `is_active == 1`, and "Desconto Exclusivo" applies to any customer. The 5% PIX discount is not added to promotional prices, which are always shown with the original price and the discount percentage (manual 6.2).

### Products

- A product is offered as available only if its status is `active` and stock is above zero; `coming_soon` and `discontinued` products are never offered as available (manual 7.3).
- Product descriptions are not sent to the model, only structured fields (name, category, price, stock, status, specs), because some descriptions contradict the product name (see 5.1).

### Shipping

- Only the Campo Grande rule is computed: free above R$ 500 and R$ 35 otherwise. The manual says "above" and "below" R$ 500 but not "exactly", so R$ 500.00 pays R$ 35 and shipping is free from R$ 500.01. For other cities the price depends on ZIP code, weight and dimensions (Correios or Jadlog), so the agent hands off to the team.

### Returns and warranty

- Exchange for preference ("up to 7 days", manual 4.3) is counted from the date the product was received.
- Defects: up to 30 days from purchase, exchange at the store (4.2); after that and up to 90 days from receipt, legal warranty with the store mediating with the manufacturer (8.1); after that, manufacturer warranty.

### Contacts and hand-off

- The agent uses phone/WhatsApp **(67) 3341-4444** and `contato@emporiodamusica.com.br` (see 5.1).
- Actions the agent cannot perform (complaints, partner stores, manager decisions, freight quotes outside Campo Grande) are handed off to the human team with the official contacts.

### Persona and repository

- The manual does not name the virtual assistant; "Clave" was created for this project.
- The provided data files are kept unchanged in `data/` with their original names. All data is fictional.

### 5.1 Inconsistencies found in the provided material

| Inconsistency | How the agent handles it |
| --- | --- |
| Manual lists two WhatsApp numbers: (67) 3341-4444 (section 1.2) and (67) 3321-4500 (section 7). | Uses 3341-4444, which also appears on the cover. |
| Manual spells the e-mail as `emporiodamusica` and `empóriodamusica` (with an accent). | Uses the version without the accent. |
| Manual section 3 says "up to 12x, minimum installment R$ 100"; section 3.1 defines three tiers. | Follows section 3.1 (more specific). |
| Defect exchange (30 days from purchase, 4.2) overlaps with legal warranty (90 days from receipt, 8.1). | Interpretation described in the Assumptions above. |
| Status contradicts stock: product 130 is `coming_soon` with stock 2 (and appears in orders); product 136 is `discontinued` with stock 13. | Status prevails over stock. |
| Products 135–144: description contradicts name and specs (e.g. "Music Man Bass 1X" described as a "Fender Jazz Bass"). | Descriptions are not used. |
| Promotions have no dates; some types and percentages differ from the manual (e.g. a 10% Black Friday, while the manual says 15–30%). | Only `is_active` decides; percentages are used as stored. |
| Order totals differ from the sum of items for orders 3 and 20; PIX orders show no 5% discount; no total includes shipping. | Stored totals are shown as they are; business rules apply to new quotes only. |
| Orders 9, 16 and 18 have installments below the manual's minimum. | Historical orders are not corrected. |
| Campo Grande orders have Correios tracking codes and 10–15 day estimates, while the manual says local delivery is by motorcycle courier in 1–3 business days. | Order data is reported as stored. |
| Customers 11 and 43 share the same e-mail. | Verification is done against the customer of the requested order, so the duplicate has no effect. |
| Categories 6, 7 and 8 (wind instruments, orchestral strings) have no products, although the manual mentions them. | The agent says they are not available at the moment and does not invent products. |
| The manual excludes "final sale" clearance items from exchanges (4.4), but the data has no such flag. | The agent cannot check it and hands off to the team. |

## 6. Example conversations

To be completed.

## 7. Known limitations and what I would do with more time

To be completed.

## 8. Use of AI assistants

To be completed.
