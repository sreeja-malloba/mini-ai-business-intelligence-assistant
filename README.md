# Mini AI Business Intelligence Assistant

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Tests
```bash
python -m unittest discover -s tests -v
```

## Architecture
Browser → Flask API → natural-language intent interpreter → fixed read-only SQL templates → SQLite → answer + supporting figures.

## Data and calculation
Revenue = quantity × unit_price − discount_amount. Only Completed transactions with quantity > 0 are included. Returned transactions and zero-quantity records are excluded. Invalid rows are skipped. The source is a PDF table, not a CSV. TXN0051 has a blank unit price in the PDF, so it is left blank in the CSV and skipped during database import.

## AI interpretation and safety
A constrained natural-language intent interpreter maps question phrases to five supported analytics intents. It uses reviewed SQL templates; it does not execute arbitrary model-generated SQL. User text is never inserted into SQL. Unsupported questions return an error instead of a guessed answer. A future version could add an LLM to classify questions into a validated intent schema.

## Limitations
Keyword-based interpretation supports limited phrasings; month comparison is limited to Jan–Jun 2026; no authentication or production deployment.

## Development notes
Edit this section to accurately describe your own process. ChatGPT can be documented as a planning, code scaffolding, debugging, and test-writing assistant. Problems: source data was a PDF and final row had a blank unit price. With another day: add an LLM intent classifier, charts, more tests, authentication, and deployment.
