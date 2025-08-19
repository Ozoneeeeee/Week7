"""
Flask Web App demonstrating:
  1) Object-Oriented Programming (OOP)
  2) Functional Programming (map, filter)
  3) Asynchronous I/O with asyncio (async routes + concurrent tasks)
  4) HTML frontend for interaction with live item table

Run locally:
  pip install Flask>=2.2
  python app.py
Then open http://127.0.0.1:5000
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field, asdict
from itertools import count
from typing import List, Iterable, Dict, Any

from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# -----------------------------
# OOP: Domain Model
# -----------------------------
_id_seq = count(1)

@dataclass
class Item:
    name: str
    price: float
    category: str
    id: int = field(default_factory=lambda: next(_id_seq))

    def apply_discount(self, percent: float) -> float:
        percent = max(0.0, min(percent, 100.0))
        discounted = round(self.price * (1.0 - percent / 100.0), 2)
        return discounted

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Inventory:
    def __init__(self, items: Iterable[Item] | None = None) -> None:
        self._items: List[Item] = list(items) if items else []

    def add(self, item: Item) -> Item:
        self._items.append(item)
        return item

    def all(self) -> List[Item]:
        return list(self._items)

    def by_category(self, category: str) -> List[Item]:
        return [i for i in self._items if i.category.lower() == category.lower()]

    def expensive(self, min_price: float) -> List[Item]:
        return [i for i in self._items if i.price >= min_price]


# Seed data
inventory = Inventory(
    [
        Item("USB-C Cable", 9.99, "electronics"),
        Item("Wireless Mouse", 24.50, "electronics"),
        Item("Notebook (A5)", 3.25, "stationery"),
        Item("Office Chair", 189.00, "furniture"),
        Item("Standing Desk", 399.99, "furniture"),
    ]
)

# -----------------------------
# Functional Programming helpers
# -----------------------------

def items_to_dicts(items: Iterable[Item]) -> List[Dict[str, Any]]:
    return list(map(lambda i: i.to_dict(), items))


def filter_items(items: Iterable[Item], *, min_price: float | None = None, category: str | None = None) -> List[Item]:
    preds = []
    if min_price is not None:
        preds.append(lambda i: i.price >= float(min_price))
    if category is not None:
        preds.append(lambda i: i.category.lower() == category.lower())

    if not preds:
        return list(items)

    def all_preds(i: Item) -> bool:
        return all(p(i) for p in preds)

    return list(filter(all_preds, items))


# -----------------------------
# AsyncIO: Simulated external calls
# -----------------------------
async def fetch_tax_rate(category: str) -> float:
    await asyncio.sleep(random.uniform(0.1, 0.4))
    base = {
        "electronics": 0.13,
        "furniture": 0.08,
        "stationery": 0.05,
    }.get(category.lower(), 0.07)
    return base


async def fetch_dynamic_discount(item_id: int) -> float:
    await asyncio.sleep(random.uniform(0.1, 0.5))
    return round(random.uniform(0, 15), 2)


async def compute_adjusted_price(item: Item) -> Dict[str, Any]:
    tax_rate, discount_pct = await asyncio.gather(
        fetch_tax_rate(item.category),
        fetch_dynamic_discount(item.id),
    )
    taxed = round(item.price * (1 + tax_rate), 2)
    final_price = round(item.apply_discount(discount_pct) * (1 + tax_rate), 2)
    return {
        "item": item.to_dict(),
        "tax_rate": tax_rate,
        "discount_percent": discount_pct,
        "taxed_price": taxed,
        "final_price": final_price,
    }


# -----------------------------
# HTML Template
# -----------------------------
INDEX_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Flask: OOP + FP + asyncio</title>
    <style>
      body{font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif; margin: 2rem; background:#f9fafb;}
      h1{color:#1f2937;}
      .card{border:1px solid #e5e7eb;border-radius:12px;padding:1rem;margin:1rem 0;background:white;box-shadow:0 2px 5px rgba(0,0,0,0.05)}
      .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}
      a.button{display:inline-block;padding:.5rem .75rem;border:1px solid #3b82f6;border-radius:8px;text-decoration:none;color:#3b82f6;font-weight:600}
      a.button:hover{background:#3b82f6;color:white}
      pre{background:#f3f4f6;padding:.5rem;border-radius:6px;}
      form input{padding:.4rem;margin:.3rem;border-radius:6px;border:1px solid #d1d5db;}
      form button{padding:.5rem 1rem;border:none;border-radius:8px;background:#3b82f6;color:white;cursor:pointer}
      form button:hover{background:#2563eb}
      table{width:100%;border-collapse:collapse;margin-top:1rem;}
      th,td{padding:.5rem;text-align:left;border-bottom:1px solid #e5e7eb;}
      th{background:#f3f4f6;}
    </style>
  </head>
  <body>
    <h1>Flask Demo: <em>OOP</em> + <em>Functional</em> + <em>asyncio</em></h1>
    <p>This mini app demonstrates:</p>
    <ul>
      <li><strong>OOP</strong>: <code>Item</code> and <code>Inventory</code> classes encapsulate data & behavior.</li>
      <li><strong>Functional programming</strong>: <code>map</code>/<code>filter</code> to transform and select items.</li>
      <li><strong>asyncio</strong>: async route computes adjusted prices via <code>asyncio.gather</code>.</li>
    </ul>

    <div class="grid">
      <div class="card">
        <h3>All items (JSON)</h3>
        <a class="button" href="/items">GET /items</a>
      </div>
      <div class="card">
        <h3>Filter by price ≥ 100</h3>
        <a class="button" href="/items/expensive?min=100">GET /items/expensive?min=100</a>
      </div>
      <div class="card">
        <h3>Filter by category=furniture</h3>
        <a class="button" href="/items/search?category=furniture">GET /items/search?category=furniture</a>
      </div>
      <div class="card">
        <h3>Async adjusted prices</h3>
        <a class="button" href="/async/quotes">GET /async/quotes</a>
      </div>
    </div>

    <div class="card">
      <h3>Create an Item</h3>
      <form method="POST" action="/items" onsubmit="submitForm(event)">
        <input type="text" name="name" placeholder="Name" required>
        <input type="number" step="0.01" name="price" placeholder="Price" required>
        <input type="text" name="category" placeholder="Category" required>
        <button type="submit">Add Item</button>
      </form>
      <pre id="responseBox">Response will appear here...</pre>
    </div>

    <div class="card">
      <h3>Current Inventory</h3>
      <table id="itemsTable">
        <thead>
          <tr><th>ID</th><th>Name</th><th>Price</th><th>Category</th></tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>

    <script>
      async function loadItems(){
        const res = await fetch('/items');
        const data = await res.json();
        const tbody = document.querySelector('#itemsTable tbody');
        tbody.innerHTML = '';
        data.forEach(item => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td>${item.id}</td><td>${item.name}</td><td>$${item.price.toFixed(2)}</td><td>${item.category}</td>`;
          tbody.appendChild(tr);
        });
      }

      async function submitForm(e){
        e.preventDefault();
        const form = e.target;
        const data = Object.fromEntries(new FormData(form).entries());
        data.price = parseFloat(data.price);
        const res = await fetch('/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
        const json = await res.json();
        document.getElementById('responseBox').textContent = JSON.stringify(json,null,2);
        form.reset();
        loadItems();
      }

      window.onload = loadItems;
    </script>
  </body>
</html>
"""

# -----------------------------
# Flask Routes
# -----------------------------
@app.get("/")
def index():
    return render_template_string(INDEX_TEMPLATE)


@app.get("/items")
def get_items():
    return jsonify(items_to_dicts(inventory.all()))


@app.get("/items/expensive")
def get_expensive():
    try:
        min_price = float(request.args.get("min", 100))
    except (TypeError, ValueError):
        min_price = 100.0
    items = inventory.expensive(min_price)
    return jsonify(items_to_dicts(items))


@app.get("/items/search")
def search_items():
    min_price = request.args.get("min")
    category = request.args.get("category")
    min_price_f = float(min_price) if min_price is not None else None
    filtered = filter_items(inventory.all(), min_price=min_price_f, category=category)
    return jsonify(items_to_dicts(filtered))


@app.post("/items")
def create_item():
    data = request.get_json(force=True, silent=True) or request.form.to_dict()
    name = data.get("name")
    price = data.get("price")
    category = data.get("category")
    if not isinstance(name, str) or not category or not price:
        return jsonify({"error": "Invalid payload. Expect name, price, category"}), 400
    try:
        price = float(price)
    except Exception:
        return jsonify({"error": "Price must be a number"}), 400
    item = inventory.add(Item(name=name.strip(), price=price, category=category.strip()))
    return jsonify(item.to_dict()), 201


@app.get("/async/quotes")
async def async_quotes():
    results = await asyncio.gather(*(compute_adjusted_price(i) for i in inventory.all()))
    return jsonify(results)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

