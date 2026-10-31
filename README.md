# Mini AI Business Intelligence Assistant

A lightweight Business Intelligence application that answers natural-language questions about sales data using Python, Flask, SQLite, and Gemini API integration.

## 1. Project Overview

The Mini AI Business Intelligence Assistant allows users to ask questions about sales transactions and receive structured answers with supporting figures.

The application supports five analytics operations:
- Total revenue analysis
- Top revenue-generating product
- Monthly revenue trends
- Top-performing region
- Revenue comparison between two months

## 2. Technology Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **AI Integration:** Google Gemini API (`google-genai`)
- **Testing:** Python unittest

## 3. Project Architecture

Browser UI → Flask API → Question Interpreter → Validated Analytics Intent → Fixed SQL Queries → SQLite Database → Structured Answer and Supporting Data → Browser UI.

Gemini is used to interpret natural-language questions into predefined analytics intents. The application validates the returned intent before executing its corresponding SQL query. A keyword-based fallback is available when Gemini is disabled or unavailable.

## 4. Setup and Installation

Clone the repository:

```bash
git clone https://github.com/sreeja-malloba/mini-ai-business-intelligence-assistant.git
cd mini-ai-business-intelligence-assistant
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Gemini API Configuration (Optional)

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODE=true
```

Obtain an API key from [Google AI Studio](https://aistudio.google.com/apikey).

Never commit or share your `.env` file.

To use the keyword-based interpreter without Gemini:

```env
GEMINI_MODE=false
```

### Run the application

```bash
python app.py
```

Open:

http://127.0.0.1:5000

## 5. Data Management

The original sales dataset was supplied as a PDF table and extracted into `data/sales_data.csv`.

The application:
- Loads the CSV data into SQLite.
- Validates dates and numeric fields.
- Skips invalid or incomplete rows.
- Prevents duplicate transaction IDs using a primary key.

The source PDF contains 51 transaction records. TXN0051 has a blank unit price and is skipped during database import, leaving 50 valid records.

### Revenue Calculation

Revenue is calculated as:

`Revenue = quantity × unit_price − discount_amount`

Only transactions with status `Completed` and quantity greater than zero are included in revenue analytics. Returned transactions are excluded.

## 6. AI Integration and Safety

The Gemini API is used to classify user questions into a restricted set of analytics intents:

- `total`
- `product`
- `monthly`
- `region`
- `compare`
- `unsupported`

The application validates the returned intent and month values before processing.

**Security measures:**
- The model does not generate or execute SQL.
- SQL queries use predefined templates.
- User input is not directly concatenated into SQL.
- Unsupported questions return an error instead of an invented answer.
- A keyword-based fallback handles questions when Gemini is disabled or unavailable.

Gemini API availability may vary, and temporary service errors such as HTTP 503 can trigger the fallback.

## 7. Testing

Run the automated test suite:

```bash
GEMINI_MODE=false python -m unittest discover -s tests -v
```

Six automated tests currently pass.

The tests cover:
- Total revenue
- Top product
- Monthly revenue
- Top region
- Invalid questions
- Month comparison edge cases

## 8. Limitations

- Natural-language interpretation depends on predefined intents.
- Month comparisons are limited to January–June 2026.
- Gemini availability depends on the external API service.
- The application does not currently implement authentication.
- The application is intended for local demonstration, not production deployment.

## 9. Development Process

ChatGPT was used as a development assistant for planning, code scaffolding, debugging, and test preparation.

Challenges encountered:
- Extracting structured transaction data from a PDF.
- Handling a missing unit price in the final transaction.
- Configuring the Flask environment and SQLite database.
- Handling Gemini API service unavailability.
- Testing the keyword fallback independently of the external API.

## 10. Future Improvements

- Add more natural-language question types.
- Improve Gemini response handling and retry mechanisms.
- Add charts and interactive dashboards.
- Expand the test suite.
- Introduce user authentication.
- Deploy the application using a production-ready server.

## 11. Repository

[GitHub Repository](https://github.com/sreeja-malloba/mini-ai-business-intelligence-assistant)
