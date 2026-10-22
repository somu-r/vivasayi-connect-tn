from flask import Flask, request, redirect, url_for, flash, render_template_string, jsonify
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-before-deployment"
DB_PATH = Path(__file__).with_name("vivasayi.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS farmers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    village TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL DEFAULT 'kg',
    description TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    society TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    quantity REAL NOT NULL DEFAULT 0 CHECK(quantity >= 0),
    updated_at TEXT NOT NULL,
    UNIQUE(society, product_id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity REAL NOT NULL CHECK(quantity > 0),
    status TEXT NOT NULL DEFAULT 'Pending',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(farmer_id) REFERENCES farmers(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE IF NOT EXISTS sms_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    message TEXT NOT NULL,
    kind TEXT NOT NULL,
    created_at TEXT NOT NULL,
    delivery_status TEXT NOT NULL DEFAULT 'DEMO ONLY'
);
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL DEFAULT 'Demo Officer'
);
"""

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM farmers").fetchone()[0] == 0:
            ts = now()
            farmers = [
                ("Kavitha", "9000000001", "Demo Village"),
                ("Murugan", "9000000002", "Demo Village"),
                ("Selvi", "9000000003", "Demo Village"),
            ]
            conn.executemany("INSERT INTO farmers(name,phone,village,created_at) VALUES(?,?,?,?)",
                             [(n,p,v,ts) for n,p,v in farmers])
            products = [
                ("Paddy seeds", "kg", "Example seed stock for demonstration"),
                ("Urea fertilizer", "bag", "Example fertilizer stock for demonstration"),
                ("DAP fertilizer", "bag", "Example fertilizer stock for demonstration"),
            ]
            conn.executemany("INSERT INTO products(name,unit,description) VALUES(?,?,?)", products)
            pids = {r["name"]: r["id"] for r in conn.execute("SELECT id,name FROM products")}
            stock = [
                ("Demo Village Cooperative Society", pids["Paddy seeds"], 250),
                ("Demo Village Cooperative Society", pids["Urea fertilizer"], 35),
                ("Demo Village Cooperative Society", pids["DAP fertilizer"], 0),
            ]
            conn.executemany("INSERT INTO stock(society,product_id,quantity,updated_at) VALUES(?,?,?,?)",
                             [(s,p,q,ts) for s,p,q in stock])
            conn.execute("""INSERT INTO announcements(title,message,created_at,created_by)
                         VALUES(?,?,?,?)""",
                         ("Welcome to Vivasayi Connect TN",
                          "Demo notice: stock figures are sample data, not official government information.",
                          ts, "Demo Officer"))

def log_sms(conn, phone, message, kind="Notification"):
    conn.execute("INSERT INTO sms_log(phone,message,kind,created_at,delivery_status) VALUES(?,?,?,?,?)",
                 (phone, message, kind, now(), "DEMO ONLY - NOT SENT"))

def layout(content, **kwargs):
    return render_template_string("""
    <!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Vivasayi Connect TN</title>
    <style>
      :root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#193329;background:#f4f8f3}
      body{margin:0}header{background:#185b3b;color:white;padding:18px max(18px,calc((100% - 1080px)/2))}
      header h1{margin:0;font-size:1.35rem}header p{margin:5px 0 0;color:#e0f0e4}
      nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}nav a{color:white;text-decoration:none;border:1px solid #ffffff55;border-radius:999px;padding:7px 11px;font-size:.9rem}
      main{max-width:1080px;margin:22px auto;padding:0 16px 40px}.notice{background:#fff2ce;border:1px solid #eed58b;border-radius:10px;padding:12px;margin-bottom:16px}
      .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}.card{background:white;border:1px solid #dce8dd;border-radius:14px;padding:17px;box-shadow:0 2px 8px #153f2510}
      h2{margin-top:0;font-size:1.2rem}h3{margin-bottom:7px}.muted{color:#607469;font-size:.92rem}.number{font-size:1.8rem;font-weight:750;color:#185b3b}
      label{display:block;font-weight:600;margin:10px 0 5px}input,select,textarea{width:100%;box-sizing:border-box;border:1px solid #bdcfc0;border-radius:8px;padding:10px;font:inherit;background:white}
      button,.btn{display:inline-block;border:0;border-radius:9px;background:#187447;color:white;padding:10px 14px;font:inherit;text-decoration:none;cursor:pointer;margin-top:12px}
      .btn.secondary,button.secondary{background:#e4efe7;color:#185b3b}.row{display:flex;gap:10px;flex-wrap:wrap}.row>*{flex:1;min-width:160px}
      table{width:100%;border-collapse:collapse;background:white}th,td{text-align:left;padding:10px;border-bottom:1px solid #e1e9e2;font-size:.92rem}th{background:#eef5ef}
      .table-wrap{overflow-x:auto;border-radius:10px;border:1px solid #dce8dd}.flash{padding:11px;border-radius:9px;background:#e0f5e5;margin-bottom:12px}
      .tag{display:inline-block;border-radius:99px;background:#e7f3e9;padding:4px 9px;font-size:.82rem}.warning{color:#9b3d26}.small{font-size:.84rem}
      footer{max-width:1080px;margin:auto;padding:0 16px 28px;color:#607469;font-size:.85rem}
    </style></head><body><header><h1>🌾 Vivasayi Connect TN</h1>
    <p>Farmer stock information · Requests · Society dashboard</p>
    <nav><a href="/">Home</a><a href="/farmer">Farmer portal</a><a href="/officer">Officer dashboard</a><a href="/stock">Stock update</a><a href="/announcements">Announcements</a><a href="/sms-log">Demo SMS log</a><a href="/ivr">Try IVR demo</a></nav>
    </header><main>
    <div class="notice"><strong>Prototype only:</strong> all village, farmer and stock data are fictional demo data. SMS is logged, not sent. Phone IVR is simulated in the browser.</div>
    {% for msg in get_flashed_messages() %}<div class="flash">{{msg}}</div>{% endfor %}
    """ + content + """</main><footer>Vivasayi Connect TN · MVP prototype · Do not use demo data for real agricultural decisions.</footer></body></html>""", **kwargs)

@app.route("/")
def home():
    with db() as conn:
        farmers = conn.execute("SELECT COUNT(*) FROM farmers").fetchone()[0]
        open_requests = conn.execute("SELECT COUNT(*) FROM requests WHERE status NOT IN ('Completed','Rejected')").fetchone()[0]
        items = conn.execute("""SELECT p.name,p.unit,s.quantity,s.updated_at FROM stock s
                              JOIN products p ON p.id=s.product_id ORDER BY p.name""").fetchall()
        recent = conn.execute("""SELECT r.id,f.name farmer,p.name product,r.quantity,p.unit,r.status,r.created_at
                               FROM requests r JOIN farmers f ON f.id=r.farmer_id
                               JOIN products p ON p.id=r.product_id ORDER BY r.id DESC LIMIT 5""").fetchall()
    return layout("""
    <div class="grid">
      <div class="card"><div class="muted">Demo farmers</div><div class="number">{{farmers}}</div></div>
      <div class="card"><div class="muted">Open requests</div><div class="number">{{open_requests}}</div></div>
      <div class="card"><div class="muted">Products tracked</div><div class="number">{{items|length}}</div></div>
    </div>
    <div class="card" style="margin-top:15px"><h2>Current demo stock</h2><div class="table-wrap"><table><tr><th>Product</th><th>Available</th><th>Last updated</th></tr>
    {% for x in items %}<tr><td>{{x.name}}</td><td>{{x.quantity|float }} {{x.unit}}</td><td>{{x.updated_at}}</td></tr>{% endfor %}
    </table></div><p class="muted">Stock numbers are illustrative only. An authorized society user would update actual stock in a production deployment.</p></div>
    <div class="card" style="margin-top:15px"><h2>Recent farmer requests</h2>
    {% if recent %}<div class="table-wrap"><table><tr><th>ID</th><th>Farmer</th><th>Product</th><th>Quantity</th><th>Status</th></tr>
    {% for r in recent %}<tr><td>#{{r.id}}</td><td>{{r.farmer}}</td><td>{{r.product}}</td><td>{{r.quantity|float }} {{r.unit}}</td><td><span class="tag">{{r.status}}</span></td></tr>{% endfor %}</table></div>{% else %}<p class="muted">No requests yet. Open Farmer portal to create a test request.</p>{% endif %}
    </div>
    """, farmers=farmers, open_requests=open_requests, items=items, recent=recent)

@app.route("/farmer", methods=["GET","POST"])
def farmer():
    with db() as conn:
        farmers = conn.execute("SELECT * FROM farmers ORDER BY name").fetchall()
        products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        stock = conn.execute("""SELECT p.name,p.unit,s.quantity,s.society,s.updated_at
                              FROM stock s JOIN products p ON p.id=s.product_id ORDER BY p.name""").fetchall()
        if request.method == "POST":
            farmer_id = request.form.get("farmer_id", type=int)
            product_id = request.form.get("product_id", type=int)
            quantity = request.form.get("quantity", type=float)
            notes = request.form.get("notes","").strip()[:300]
            f = conn.execute("SELECT * FROM farmers WHERE id=?", (farmer_id,)).fetchone()
            p = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            if not f or not p or not quantity or quantity <= 0:
                flash("Please select a farmer/product and enter a quantity greater than zero.")
                return redirect(url_for("farmer"))
            ts = now()
            cur = conn.execute("""INSERT INTO requests(farmer_id,product_id,quantity,status,notes,created_at,updated_at)
                                  VALUES(?,?,?,'Pending',?,?,?)""",
                               (farmer_id,product_id,quantity,notes,ts,ts))
            rid = cur.lastrowid
            log_sms(conn, f["phone"], f"Vivasayi Connect demo: request #{rid} received for {quantity:g} {p['unit']} {p['name']}. Status: Pending.")
            flash(f"Request #{rid} created. Confirmation added to demo SMS log for {f['phone']} (not actually sent).")
            return redirect(url_for("farmer"))
        requests_list = conn.execute("""SELECT r.id,f.name farmer,f.phone,p.name product,r.quantity,p.unit,r.status,r.created_at
                         FROM requests r JOIN farmers f ON f.id=r.farmer_id JOIN products p ON p.id=r.product_id
                         ORDER BY r.id DESC LIMIT 20""").fetchall()
    return layout("""
    <div class="grid"><section class="card"><h2>Check stock / request supplies</h2>
    <form method="post">
      <label>Demo farmer</label><select name="farmer_id" required>{% for f in farmers %}<option value="{{f.id}}">{{f.name}} — {{f.village}} ({{f.phone}})</option>{% endfor %}</select>
      <label>Product</label><select name="product_id" required>{% for p in products %}<option value="{{p.id}}">{{p.name}} ({{p.unit}})</option>{% endfor %}</select>
      <label>Quantity needed</label><input type="number" name="quantity" min="0.1" step="0.1" required placeholder="e.g. 100">
      <label>Notes (optional)</label><textarea name="notes" rows="2" placeholder="Season / preferred collection date"></textarea>
      <button type="submit">Register request</button>
    </form></section>
    <section class="card"><h2>Stock availability</h2>{% for s in stock %}<p><strong>{{s.name}}</strong><br><span class="number" style="font-size:1.25rem">{{s.quantity|float }} {{s.unit}}</span><br><span class="muted">{{s.society}} · Updated {{s.updated_at}}</span></p>{% endfor %}</section></div>
    <div class="card" style="margin-top:15px"><h2>Recent requests</h2><div class="table-wrap"><table><tr><th>ID</th><th>Farmer</th><th>Product</th><th>Quantity</th><th>Status</th><th>Created</th></tr>
    {% for r in requests_list %}<tr><td>#{{r.id}}</td><td>{{r.farmer}}</td><td>{{r.product}}</td><td>{{r.quantity|float }} {{r.unit}}</td><td>{{r.status}}</td><td>{{r.created_at}}</td></tr>{% else %}<tr><td colspan="6">No requests yet.</td></tr>{% endfor %}</table></div></div>
    """, farmers=farmers, products=products, stock=stock, requests_list=requests_list)

@app.route("/officer", methods=["GET","POST"])
def officer():
    statuses = ["Pending","Under review","Approved","Dispatched","Completed","Rejected"]
    with db() as conn:
        if request.method == "POST":
            rid = request.form.get("request_id", type=int)
            status = request.form.get("status","")
            if status not in statuses:
                flash("Invalid status.")
                return redirect(url_for("officer"))
            r = conn.execute("""SELECT r.*,f.phone,f.name farmer,p.name product,p.unit FROM requests r
                              JOIN farmers f ON f.id=r.farmer_id JOIN products p ON p.id=r.product_id WHERE r.id=?""",(rid,)).fetchone()
            if not r:
                flash("Request not found.")
                return redirect(url_for("officer"))
            conn.execute("UPDATE requests SET status=?,updated_at=? WHERE id=?",(status,now(),rid))
            log_sms(conn,r["phone"],f"Vivasayi Connect demo: request #{rid} ({r['product']}) status updated to {status}.","Status update")
            flash(f"Request #{rid} updated to {status}; demo SMS logged (not sent).")
            return redirect(url_for("officer"))
        requests_list = conn.execute("""SELECT r.*,f.name farmer,f.phone,p.name product,p.unit FROM requests r
                                      JOIN farmers f ON f.id=r.farmer_id JOIN products p ON p.id=r.product_id
                                      ORDER BY CASE r.status WHEN 'Pending' THEN 0 WHEN 'Under review' THEN 1 ELSE 2 END,r.id DESC""").fetchall()
        demand = conn.execute("""SELECT p.name,p.unit,COUNT(r.id) request_count,COALESCE(SUM(CASE WHEN r.status NOT IN ('Completed','Rejected') THEN r.quantity ELSE 0 END),0) open_qty
                               FROM products p LEFT JOIN requests r ON r.product_id=p.id GROUP BY p.id ORDER BY p.name""").fetchall()
        shortages = conn.execute("""SELECT p.name,p.unit,s.quantity FROM stock s JOIN products p ON p.id=s.product_id WHERE s.quantity<=10 ORDER BY s.quantity""").fetchall()
    return layout("""
    <div class="grid">
    <div class="card"><h2>Demand summary</h2>{% for d in demand %}<p><strong>{{d.name}}</strong><br>{{d.request_count}} requests · {{d.open_qty|float }} {{d.unit}} open demand</p>{% endfor %}</div>
    <div class="card"><h2>Low-stock alerts</h2>{% for s in shortages %}<p class="warning"><strong>{{s.name}}</strong>: {{s.quantity|float }} {{s.unit}} remaining</p>{% else %}<p>No low-stock alerts.</p>{% endfor %}<p class="muted">Demo threshold: 10 units. Production threshold should vary by product.</p></div>
    </div>
    <div class="card" style="margin-top:15px"><h2>Manage farmer requests</h2><div class="table-wrap"><table><tr><th>ID</th><th>Farmer</th><th>Product</th><th>Qty</th><th>Current status</th><th>Update</th></tr>
    {% for r in requests_list %}<tr><td>#{{r.id}}</td><td>{{r.farmer}}<br><span class="muted">{{r.phone}}</span></td><td>{{r.product}}</td><td>{{r.quantity|float }} {{r.unit}}</td><td>{{r.status}}</td><td><form method="post" style="min-width:170px"><input type="hidden" name="request_id" value="{{r.id}}"><select name="status">{% for s in statuses %}<option {% if s==r.status %}selected{% endif %}>{{s}}</option>{% endfor %}</select><button>Save status</button></form></td></tr>{% else %}<tr><td colspan="6">No requests yet.</td></tr>{% endfor %}</table></div></div>
    """, requests_list=requests_list, demand=demand, shortages=shortages, statuses=statuses)

@app.route("/stock", methods=["GET","POST"])
def stock_update():
    with db() as conn:
        if request.method == "POST":
            stock_id = request.form.get("stock_id", type=int)
            qty = request.form.get("quantity", type=float)
            if qty is None or qty < 0:
                flash("Quantity must be zero or greater.")
                return redirect(url_for("stock_update"))
            item = conn.execute("""SELECT s.*,p.name,p.unit FROM stock s JOIN products p ON p.id=s.product_id WHERE s.id=?""",(stock_id,)).fetchone()
            if not item:
                flash("Stock record not found.")
                return redirect(url_for("stock_update"))
            conn.execute("UPDATE stock SET quantity=?,updated_at=? WHERE id=?",(qty,now(),stock_id))
            if qty <= 10:
                conn.execute("""INSERT INTO announcements(title,message,created_at,created_by) VALUES(?,?,?,?)""",
                             ("Low stock alert: "+item["name"],f"Demo alert: {item['name']} stock is {qty:g} {item['unit']}. Please review supply needs.",now(),"Demo System"))
            flash(f"Stock updated for {item['name']}.")
            return redirect(url_for("stock_update"))
        items = conn.execute("""SELECT s.id,s.society,s.quantity,s.updated_at,p.name,p.unit FROM stock s JOIN products p ON p.id=s.product_id ORDER BY p.name""").fetchall()
    return layout("""
    <div class="card"><h2>Update society stock</h2><p class="muted">Prototype has no login or role security. Do not expose this page publicly.</p>
    {% for x in items %}<form method="post" class="row" style="align-items:end;border-bottom:1px solid #e1e9e2;padding:8px 0"><input type="hidden" name="stock_id" value="{{x.id}}"><div><strong>{{x.name}}</strong><div class="muted">{{x.society}} · Current {{x.quantity|float }} {{x.unit}}</div></div><div><label>New quantity ({{x.unit}})</label><input type="number" min="0" step="0.1" name="quantity" value="{{x.quantity}}" required></div><div><button>Update stock</button></div></form>{% endfor %}
    </div>
    """, items=items)

@app.route("/announcements", methods=["GET","POST"])
def announcements():
    with db() as conn:
        if request.method == "POST":
            title = request.form.get("title","").strip()[:120]
            message = request.form.get("message","").strip()[:500]
            if not title or not message:
                flash("Title and message are required.")
                return redirect(url_for("announcements"))
            conn.execute("INSERT INTO announcements(title,message,created_at,created_by) VALUES(?,?,?,?)",(title,message,now(),"Demo Officer"))
            farmers = conn.execute("SELECT phone FROM farmers").fetchall()
            for f in farmers:
                log_sms(conn,f["phone"],f"Vivasayi Connect demo announcement: {title} — {message}","Announcement")
            flash(f"Announcement saved and {len(farmers)} demo SMS entries created. No real SMS was sent.")
            return redirect(url_for("announcements"))
        rows = conn.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
    return layout("""
    <div class="grid"><section class="card"><h2>Create stock announcement</h2><form method="post">
      <label>Title</label><input name="title" maxlength="120" required placeholder="e.g. Paddy seeds available">
      <label>Message</label><textarea name="message" maxlength="500" rows="4" required placeholder="Include product, society, quantity, date and contact information"></textarea>
      <button>Publish to demo SMS log</button></form><p class="muted">Production needs verified stock, consent/communication preferences, approved SMS provider and applicable messaging compliance.</p></section>
    <section class="card"><h2>Good announcement format</h2><p>“Demo notice: Paddy seeds available at Demo Village Cooperative Society. Sample quantity: 250 kg. Please confirm availability before visiting.”</p><p class="muted">Never present sample data as official government stock information.</p></section></div>
    <div class="card" style="margin-top:15px"><h2>Published announcements</h2>{% for a in rows %}<div style="padding:12px 0;border-bottom:1px solid #e1e9e2"><strong>{{a.title}}</strong><p>{{a.message}}</p><span class="muted">{{a.created_at}} · {{a.created_by}}</span></div>{% else %}<p>No announcements.</p>{% endfor %}</div>
    """, rows=rows)

@app.route("/sms-log")
def sms_log():
    with db() as conn:
        rows = conn.execute("SELECT * FROM sms_log ORDER BY id DESC LIMIT 100").fetchall()
    return layout("""
    <div class="card"><h2>Demo SMS log</h2><p class="muted">These messages are stored in the database only. Nothing has been sent to a mobile phone.</p>
    <div class="table-wrap"><table><tr><th>Time</th><th>Phone</th><th>Type</th><th>Message</th><th>Delivery</th></tr>{% for x in rows %}<tr><td>{{x.created_at}}</td><td>{{x.phone}}</td><td>{{x.kind}}</td><td>{{x.message}}</td><td>{{x.delivery_status}}</td></tr>{% else %}<tr><td colspan="5">No demo SMS logged yet.</td></tr>{% endfor %}</table></div></div>
    """, rows=rows)

@app.route("/ivr")
def ivr():
    return layout("""
    <div class="card"><h2>Try the phone IVR flow (browser simulation)</h2>
    <p>Imagine calling the helpline. Choose a menu option below; this uses the demo stock database and does not place a phone call.</p>
    <div class="grid">
      <div class="card"><h3>Press 1 — Check stock</h3><p>Choose a product to hear its current demo availability.</p>
      <label>Product</label><select id="product"><option value="1">Paddy seeds</option><option value="2">Urea fertilizer</option><option value="3">DAP fertilizer</option></select><button onclick="checkStock()">Play stock response</button><p id="stockResult" aria-live="polite"></p></div>
      <div class="card"><h3>Press 2 — Request a callback</h3><p>Simulation only. Real callback requires a voice provider.</p><label>Demo phone</label><select id="phone"><option>9000000001</option><option>9000000002</option><option>9000000003</option></select><button onclick="callbackDemo()">Request demo callback</button><p id="callbackResult" aria-live="polite"></p></div>
    </div>
    <p class="muted">Real IVR integration normally uses a provider webhook to receive call events/DTMF, then calls a secure API to look up stock and play a recorded or text-to-speech response.</p></div>
    <script>
      async function checkStock(){let id=document.getElementById('product').value;let r=await fetch('/api/ivr/stock?product_id='+id);let d=await r.json();document.getElementById('stockResult').textContent=d.spoken_response;}
      async function callbackDemo(){let phone=document.getElementById('phone').value;let r=await fetch('/api/ivr/callback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone})});let d=await r.json();document.getElementById('callbackResult').textContent=d.message;}
    </script>
    """)

@app.route("/api/ivr/stock")
def ivr_stock_api():
    product_id = request.args.get("product_id", type=int)
    with db() as conn:
        row = conn.execute("""SELECT p.name,p.unit,s.quantity,s.society FROM products p
                            JOIN stock s ON s.product_id=p.id WHERE p.id=?""",(product_id,)).fetchone()
    if not row:
        return jsonify(error="Product not found"), 404
    if row["quantity"] <= 0:
        spoken = f"Demo information. {row['name']} is currently shown as out of stock at {row['society']}. Please register demand or contact the society."
    else:
        spoken = f"Demo information. {row['name']} stock is {row['quantity']:g} {row['unit']} at {row['society']}. Please confirm availability before travelling."
    return jsonify(product=row["name"], quantity=row["quantity"], unit=row["unit"], spoken_response=spoken, demo_only=True)

@app.route("/api/ivr/callback", methods=["POST"])
def ivr_callback_api():
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone",""))
    with db() as conn:
        farmer = conn.execute("SELECT * FROM farmers WHERE phone=?",(phone,)).fetchone()
        if not farmer:
            return jsonify(message="Demo phone number not found."), 404
        log_sms(conn, phone, "Demo IVR: callback request captured. No actual call was placed.", "IVR callback")
    return jsonify(message=f"Demo callback request recorded for {phone}. No actual call was placed.", demo_only=True)

@app.route("/health")
def health():
    return jsonify(status="ok", service="Vivasayi Connect TN", demo_mode=True)

if __name__ == "__main__":
    init_db()
    print("Vivasayi Connect TN is starting in DEMO mode.")
    print("Open http://127.0.0.1:5000")
    app.run(debug=True)
