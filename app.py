
import csv
import re
import sqlite3
import os
import json

from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

ROOT = Path(__file__).resolve().parent
DB = ROOT / "sales.db"
CSV = ROOT / "data" / "sales_data.csv"

app = Flask(__name__)

# Gemini configuration
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODE = os.getenv("GEMINI_MODE", "true").lower() == "true"

client = genai.Client(api_key=API_KEY) if API_KEY else None

VALID_MONTHS = {
    "january", "february", "march",
    "april", "may", "june"
}

VALID_INTENTS = {
    "total", "product", "monthly",
    "region", "compare", "unsupported"
}


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def initialize_database():
    with db() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS sales(
            transaction_id TEXT PRIMARY KEY,
            order_date TEXT NOT NULL,
            product TEXT NOT NULL,
            category TEXT NOT NULL,
            region TEXT NOT NULL,
            sales_channel TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount_amount REAL NOT NULL,
            status TEXT NOT NULL
        )
        """)

        if c.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0:
            with open(CSV, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    try:
                        d = datetime.strptime(
                            r["order_date"], "%d-%m-%Y"
                        ).strftime("%Y-%m-%d")

                        q = int(r["quantity"])
                        p = float(r["unit_price"])
                        disc = float(r["discount_amount"])

                        if min(q, p, disc) < 0:
                            continue

                        c.execute(
                            "INSERT OR IGNORE INTO sales VALUES(?,?,?,?,?,?,?,?,?,?)",
                            (
                                r["transaction_id"], d, r["product"],
                                r["category"], r["region"],
                                r["sales_channel"], q, p, disc, r["status"]
                            )
                        )

                    except (ValueError, TypeError, KeyError):
                        continue


def query(sql, params=()):
    if not sql.lstrip().upper().startswith("SELECT"):
        raise ValueError("SELECT only")

    with db() as c:
        return [
            dict(x)
            for x in c.execute(sql, params).fetchall()
        ]


# Original keyword interpreter (fallback)
def interpret_keywords(q):
    s = q.lower()

    if any(x in s for x in [
        "total revenue", "overall revenue",
        "total sales", "revenue generated"
    ]):
        return "total", []

    if any(x in s for x in [
        "highest revenue product", "top product",
        "best selling product", "which product",
        "product generated"
    ]):
        return "product", []

    if any(x in s for x in [
        "monthly", "month-wise", "month wise", "trend"
    ]):
        return "monthly", []

    if any(x in s for x in [
        "region", "which area", "highest sales area"
    ]):
        return "region", []

    if any(x in s for x in [
        "compare", "change between",
        "revenue change", "between two months"
    ]):
        months = re.findall(
            r"\b(january|february|march|april|may|june)\b", s
        )
        return "compare", months

    return None, []


# Gemini classifies the question; it NEVER generates SQL
def classify_with_gemini(question):
    if not GEMINI_MODE or client is None:
        return None

    prompt = f"""
You classify questions about a sales database.

Choose exactly one intent:
- total: asks for total or overall revenue
- product: asks which product generated the highest revenue
- monthly: asks for monthly revenue or a monthly trend
- region: asks which region generated the highest revenue
- compare: asks to compare revenue between two months
- unsupported: anything else

Available months: January, February, March, April, May, June.

Return only a JSON object in this format:
{{
  "intent": "compare",
  "months": ["january", "february"]
}}

Rules:
- Never generate SQL.
- For intents other than compare, months must be an empty array.
- For compare, return exactly two months mentioned in the question.
- Use lowercase month names.
- If the question is unrelated or unclear, use unsupported.

User question: {question}
"""

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        result = json.loads(response.text)

        intent = result.get("intent")
        months = result.get("months", [])

        if intent not in VALID_INTENTS:
            return None

        if not isinstance(months, list):
            return None

        if any(
            not isinstance(m, str) or m not in VALID_MONTHS
            for m in months
        ):
            return None

        if intent == "compare" and len(months) != 2:
            return None

        if intent != "compare":
            months = []

        return intent, months

    except Exception as e:
        print("Gemini unavailable; using keyword fallback:", e)
        return None


def interpret(q):
    # Try Gemini first
    gemini_result = classify_with_gemini(q)

    if gemini_result is not None:
        return gemini_result

    # Use original interpreter if Gemini is unavailable
    return interpret_keywords(q)


def answer(q):
    intent, months = interpret(q)
    base = "status='Completed' AND quantity>0"

    if intent == "total":
        rows = query(f"""
            SELECT
                ROUND(SUM(quantity*unit_price-discount_amount),2)
                total_revenue,
                COUNT(*) transaction_count
            FROM sales
            WHERE {base}
        """)

        return {
            "answer": f"Total revenue is ₹{(rows[0]['total_revenue'] or 0):,.2f}.",
            "supporting_data": rows,
            "intent": "total_revenue",
            "calculation": "quantity × unit_price − discount_amount"
        }, 200

    if intent == "product":
        rows = query(f"""
            SELECT product,
            ROUND(SUM(quantity*unit_price-discount_amount),2) revenue
            FROM sales
            WHERE {base}
            GROUP BY product
            ORDER BY revenue DESC
            LIMIT 5
        """)

        return {
            "answer": f"{rows[0]['product']} generated the highest revenue: ₹{rows[0]['revenue']:,.2f}.",
            "supporting_data": rows,
            "intent": "top_product"
        }, 200

    if intent == "monthly":
        rows = query(f"""
            SELECT strftime('%Y-%m',order_date) month,
            ROUND(SUM(quantity*unit_price-discount_amount),2) revenue
            FROM sales
            WHERE {base}
            GROUP BY month
            ORDER BY month
        """)

        return {
            "answer": "Here is the monthly revenue trend.",
            "supporting_data": rows,
            "intent": "monthly_trend"
        }, 200

    if intent == "region":
        rows = query(f"""
            SELECT region,
            ROUND(SUM(quantity*unit_price-discount_amount),2) revenue
            FROM sales
            WHERE {base}
            GROUP BY region
            ORDER BY revenue DESC
        """)

        return {
            "answer": f"{rows[0]['region']} generated the highest sales: ₹{rows[0]['revenue']:,.2f}.",
            "supporting_data": rows,
            "intent": "top_region"
        }, 200

    if intent == "compare":
        mp = {
            "january": "2026-01",
            "february": "2026-02",
            "march": "2026-03",
            "april": "2026-04",
            "may": "2026-05",
            "june": "2026-06"
        }

        if len(months) != 2:
            return {
                "error": "Mention two months, e.g. compare January and February."
            }, 400

        a, b = mp[months[0]], mp[months[1]]

        rows = query(f"""
            SELECT strftime('%Y-%m',order_date) month,
            ROUND(SUM(quantity*unit_price-discount_amount),2) revenue
            FROM sales
            WHERE {base}
            AND strftime('%Y-%m',order_date) IN (?,?)
            GROUP BY month
            ORDER BY month
        """, (a, b))

        v = {x["month"]: x["revenue"] or 0 for x in rows}
        delta = v.get(b, 0) - v.get(a, 0)

        pct = delta / v[a] * 100 if v.get(a) else None

        word = (
            "increased" if delta > 0
            else "decreased" if delta < 0
            else "did not change"
        )

        msg = (
            f"Revenue {word} by ₹{abs(delta):,.2f}"
            + (f" ({abs(pct):.2f}%)" if pct is not None else "")
            + f" from {months[0].title()} to {months[1].title()}."
        )

        return {
            "answer": msg,
            "supporting_data": rows,
            "intent": "month_comparison"
        }, 200

    return {
        "error": "Unsupported question. Try total revenue, top product, monthly trend, top region, or compare two months."
    }, 400


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
def ask():
    d = request.get_json(silent=True) or {}
    q = d.get("question", "")

    if not isinstance(q, str) or len(q) > 500:
        return jsonify({
            "error": "Question must be text under 500 characters."
        }), 400

    result, status = answer(q)
    return jsonify(result), status


@app.route("/api/health")
def health():
    with db() as c:
        n = c.execute("SELECT COUNT(*) FROM sales").fetchone()[0]

    return jsonify({
        "status": "ok",
        "records_loaded": n
    })


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
