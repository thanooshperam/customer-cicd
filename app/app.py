from flask import Flask, jsonify, request
import os

from customer_repository import get_customers

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV")


@app.route("/")
def home():
    return jsonify({
        "application": "customer-app",
        "version": VERSION,
        "environment": ENVIRONMENT
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "version": VERSION,
        "environment": ENVIRONMENT
    }), 200


@app.route("/version")
def version():
    return jsonify({
        "version": VERSION
    })


@app.route("/customers/search")
def search_customers():
    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify({
            "error": "Search query is required"
        }), 400

    customers = get_customers()

    results = [
        customer
        for customer in customers
        if query in customer["name"].lower()
        or query in customer["email"].lower()
        or query in customer["city"].lower()
    ]

    return jsonify({
        "query": query,
        "count": len(results),
        "customers": results
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)