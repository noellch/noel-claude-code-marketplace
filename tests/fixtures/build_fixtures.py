"""Build two fixture repos for measuring code-review false positives / negatives.

orders-clean  : feature branch with no defects.
orders-subtle : same feature branch, three planted logic bugs with no grep signature:
  B1 has_more computed as len(rows) == page_size (wrong at exact page boundary)
  B2 reports.first_order_date relies on fetch_orders being oldest-first; the branch
     flips the ORDER BY to newest-first and does not touch reports.py
  B3 ORDER BY created_at DESC without a tiebreaker under LIMIT/OFFSET pagination

Refuses to run if the target dirs exist. Never deletes anything.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
CLEAN = ROOT / "orders-clean"
SUBTLE = ROOT / "orders-subtle"

for d in (CLEAN, SUBTLE):
    if d.exists():
        sys.exit(f"refusing: {d} exists")


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def put(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def commit(repo, msg):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


# ---------------------------------------------------------------- main (shared)

CLAUDE_MD = """# orders-svc conventions

- All SQL lives in `app/repo.py`. Handlers in `app/api.py` and reports in `app/reports.py` call repo functions and never build SQL strings.
- Tests assert concrete values. `assertTrue(result)` on a collection is not a test.
- Renaming a public function in `app/repo.py` requires updating every caller, including `scripts/`.
- Run tests with `python3 -m unittest discover -s tests`.
"""

DB_PY = """import sqlite3


def connect(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def execute(conn, sql, params=()):
    cur = conn.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]
"""

REPO_MAIN = """from app import db


def get_order(conn, order_id):
    rows = db.execute(conn, "SELECT * FROM orders WHERE id = ?", (order_id,))
    return rows[0] if rows else None


def fetch_orders(conn, customer_id):
    return db.execute(
        conn,
        "SELECT * FROM orders WHERE customer_id = ? ORDER BY id",
        (customer_id,),
    )


def get_customer(conn, customer_id):
    rows = db.execute(conn, "SELECT * FROM customers WHERE id = ?", (customer_id,))
    return rows[0] if rows else None
"""

API_MAIN = """from app import repo


def order_detail(conn, order_id):
    order = repo.get_order(conn, order_id)
    if order is None:
        return {"error": "not_found"}, 404
    return order, 200


def customer_orders(conn, customer_id):
    return repo.fetch_orders(conn, customer_id), 200
"""

REPORTS_MAIN = """from app import repo


def first_order_date(conn, customer_id):
    \"\"\"Date (YYYY-MM-DD) of the customer's earliest order, or None. Used by the cohort report.\"\"\"
    orders = repo.fetch_orders(conn, customer_id)
    if not orders:
        return None
    return orders[0]["created_at"][:10]
"""

EXPORT_MAIN = """import csv
import sys

from app import db
from app.repo import fetch_orders


def main(customer_id):
    conn = db.connect("orders.db")
    writer = csv.writer(sys.stdout)
    for order in fetch_orders(conn, customer_id):
        writer.writerow([order["id"], order["total"]])


if __name__ == "__main__":
    main(int(sys.argv[1]))
"""

EXPORT_C3 = """import csv
import sys

from app import db
from app.repo import fetch_orders


def main(customer_id):
    conn = db.connect("orders.db")
    writer = csv.writer(sys.stdout)
    writer.writerow(["id", "total", "created_at"])
    for order in fetch_orders(conn, customer_id):
        writer.writerow([order["id"], order["total"], order["created_at"]])


if __name__ == "__main__":
    main(int(sys.argv[1]))
"""

SCHEMA = '''SCHEMA = """
CREATE TABLE customers (id INTEGER PRIMARY KEY, email TEXT);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, total REAL, created_at TEXT);
INSERT INTO customers VALUES (1, 'a@x.io'), (2, 'b@x.io');
INSERT INTO orders VALUES
  (1, 1, 9.5, '2026-01-05T10:00:00'),
  (2, 1, 20.0, '2026-03-10T09:30:00'),
  (3, 2, 5.0, '2026-02-01T00:00:00');
"""
'''

TEST_API_MAIN = f"""import unittest

from app import api, db

{SCHEMA}

class ApiTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect()
        self.conn.executescript(SCHEMA)

    def test_order_detail(self):
        body, status = api.order_detail(self.conn, 1)
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 9.5)

    def test_order_detail_missing(self):
        body, status = api.order_detail(self.conn, 99)
        self.assertEqual(status, 404)
        self.assertEqual(body, {{"error": "not_found"}})

    def test_customer_orders(self):
        body, status = api.customer_orders(self.conn, 1)
        self.assertEqual(status, 200)
        self.assertEqual([o["id"] for o in body], [1, 2])
"""

TEST_REPORTS_MAIN = f"""import unittest

from app import db, reports

{SCHEMA}

class ReportsTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect()
        self.conn.executescript(SCHEMA)

    def test_first_order_date(self):
        self.assertEqual(reports.first_order_date(self.conn, 2), "2026-02-01")

    def test_first_order_date_no_orders(self):
        self.assertIsNone(reports.first_order_date(self.conn, 42))
"""


def build_main(repo):
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "fixture@example.com")
    git(repo, "config", "user.name", "fixture")
    put(repo, "CLAUDE.md", CLAUDE_MD)
    put(repo, "app/__init__.py", "")
    put(repo, "app/db.py", DB_PY)
    put(repo, "app/repo.py", REPO_MAIN)
    put(repo, "app/api.py", API_MAIN)
    put(repo, "app/reports.py", REPORTS_MAIN)
    put(repo, "scripts/export.py", EXPORT_MAIN)
    put(repo, "tests/test_api.py", TEST_API_MAIN)
    put(repo, "tests/test_reports.py", TEST_REPORTS_MAIN)
    commit(repo, "init: orders service with repo layer, reports, export script, tests")


# ---------------------------------------------------------------- c1: pagination

REPO_C1 = """from app import db


def get_order(conn, order_id):
    rows = db.execute(conn, "SELECT * FROM orders WHERE id = ?", (order_id,))
    return rows[0] if rows else None


def fetch_orders(conn, customer_id, limit=None, offset=0):
    sql = "SELECT * FROM orders WHERE customer_id = ? ORDER BY id"
    params = [customer_id]
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return db.execute(conn, sql, tuple(params))


def get_customer(conn, customer_id):
    rows = db.execute(conn, "SELECT * FROM customers WHERE id = ?", (customer_id,))
    return rows[0] if rows else None
"""

API_C1_CLEAN = """from app import repo

MAX_PAGE_SIZE = 100


def order_detail(conn, order_id):
    order = repo.get_order(conn, order_id)
    if order is None:
        return {"error": "not_found"}, 404
    return order, 200


def customer_orders(conn, customer_id, page=1, page_size=20):
    \"\"\"page is 1-based. Fetches one extra row so has_more never needs a COUNT.\"\"\"
    if page < 1 or not 1 <= page_size <= MAX_PAGE_SIZE:
        return {"error": "bad_page"}, 400
    offset = (page - 1) * page_size
    rows = repo.fetch_orders(conn, customer_id, limit=page_size + 1, offset=offset)
    return {"items": rows[:page_size], "has_more": len(rows) > page_size}, 200
"""

API_C1_SUBTLE = """from app import repo

MAX_PAGE_SIZE = 100


def order_detail(conn, order_id):
    order = repo.get_order(conn, order_id)
    if order is None:
        return {"error": "not_found"}, 404
    return order, 200


def customer_orders(conn, customer_id, page=1, page_size=20):
    \"\"\"page is 1-based.\"\"\"
    if page < 1 or not 1 <= page_size <= MAX_PAGE_SIZE:
        return {"error": "bad_page"}, 400
    offset = (page - 1) * page_size
    rows = repo.fetch_orders(conn, customer_id, limit=page_size, offset=offset)
    return {"items": rows, "has_more": len(rows) == page_size}, 200
"""


def test_api(order_ids_page1_size1, order_ids_page2_size1, order_ids_size5, extra=""):
    return f"""import unittest

from app import api, db

{SCHEMA}

class ApiTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect()
        self.conn.executescript(SCHEMA)

    def test_order_detail(self):
        body, status = api.order_detail(self.conn, 1)
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 9.5)

    def test_order_detail_missing(self):
        body, status = api.order_detail(self.conn, 99)
        self.assertEqual(status, 404)
        self.assertEqual(body, {{"error": "not_found"}})

    def test_customer_orders_first_page(self):
        body, status = api.customer_orders(self.conn, 1, page=1, page_size=1)
        self.assertEqual(status, 200)
        self.assertEqual([o["id"] for o in body["items"]], {order_ids_page1_size1})
        self.assertIs(body["has_more"], True)

    def test_customer_orders_all_on_one_page(self):
        body, status = api.customer_orders(self.conn, 1, page=1, page_size=5)
        self.assertEqual(status, 200)
        self.assertEqual([o["id"] for o in body["items"]], {order_ids_size5})
        self.assertIs(body["has_more"], False)

    def test_customer_orders_bad_page(self):
        self.assertEqual(api.customer_orders(self.conn, 1, page=0)[1], 400)
        self.assertEqual(api.customer_orders(self.conn, 1, page_size=0)[1], 400)
        self.assertEqual(api.customer_orders(self.conn, 1, page_size=101)[1], 400)
{extra}"""


EXTRA_CLEAN = """
    def test_customer_orders_last_page_exact_boundary(self):
        body, status = api.customer_orders(self.conn, 1, page=2, page_size=1)
        self.assertEqual(status, 200)
        self.assertEqual([o["id"] for o in body["items"]], {page2})
        self.assertIs(body["has_more"], False)

    def test_customer_orders_past_end(self):
        body, status = api.customer_orders(self.conn, 1, page=3, page_size=1)
        self.assertEqual(status, 200)
        self.assertEqual(body["items"], [])
        self.assertIs(body["has_more"], False)
"""


def build_c1(repo, clean):
    put(repo, "app/repo.py", REPO_C1)
    put(repo, "app/api.py", API_C1_CLEAN if clean else API_C1_SUBTLE)
    extra = EXTRA_CLEAN.replace("{page2}", "[2]") if clean else ""
    put(repo, "tests/test_api.py", test_api("[1]", "[2]", "[1, 2]", extra))
    commit(repo, "feat: paginate customer orders (1-based page, has_more)")


# ---------------------------------------------------------------- c2: newest first

REPO_C2_CLEAN = """from app import db


def get_order(conn, order_id):
    rows = db.execute(conn, "SELECT * FROM orders WHERE id = ?", (order_id,))
    return rows[0] if rows else None


def fetch_orders(conn, customer_id, limit=None, offset=0):
    \"\"\"Newest first. id is the tiebreaker so pagination is stable when created_at ties.\"\"\"
    sql = "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC, id DESC"
    params = [customer_id]
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return db.execute(conn, sql, tuple(params))


def earliest_order(conn, customer_id):
    rows = db.execute(
        conn,
        "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at ASC, id ASC LIMIT 1",
        (customer_id,),
    )
    return rows[0] if rows else None


def get_customer(conn, customer_id):
    rows = db.execute(conn, "SELECT * FROM customers WHERE id = ?", (customer_id,))
    return rows[0] if rows else None
"""

REPO_C2_SUBTLE = """from app import db


def get_order(conn, order_id):
    rows = db.execute(conn, "SELECT * FROM orders WHERE id = ?", (order_id,))
    return rows[0] if rows else None


def fetch_orders(conn, customer_id, limit=None, offset=0):
    \"\"\"Newest first.\"\"\"
    sql = "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC"
    params = [customer_id]
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return db.execute(conn, sql, tuple(params))


def get_customer(conn, customer_id):
    rows = db.execute(conn, "SELECT * FROM customers WHERE id = ?", (customer_id,))
    return rows[0] if rows else None
"""

REPORTS_C2_CLEAN = """from app import repo


def first_order_date(conn, customer_id):
    \"\"\"Date (YYYY-MM-DD) of the customer's earliest order, or None. Used by the cohort report.\"\"\"
    order = repo.earliest_order(conn, customer_id)
    if order is None:
        return None
    return order["created_at"][:10]
"""

TEST_REPORTS_C2_CLEAN = f"""import unittest

from app import db, reports

{SCHEMA}

class ReportsTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect()
        self.conn.executescript(SCHEMA)

    def test_first_order_date(self):
        self.assertEqual(reports.first_order_date(self.conn, 2), "2026-02-01")

    def test_first_order_date_picks_earliest_of_many(self):
        self.assertEqual(reports.first_order_date(self.conn, 1), "2026-01-05")

    def test_first_order_date_no_orders(self):
        self.assertIsNone(reports.first_order_date(self.conn, 42))
"""


def build_c2(repo, clean):
    if clean:
        put(repo, "app/repo.py", REPO_C2_CLEAN)
        put(repo, "app/reports.py", REPORTS_C2_CLEAN)
        put(repo, "tests/test_reports.py", TEST_REPORTS_C2_CLEAN)
        extra = EXTRA_CLEAN.replace("{page2}", "[1]")
        put(repo, "tests/test_api.py", test_api("[2]", "[1]", "[2, 1]", extra))
        commit(repo, "feat: newest orders first; reports use earliest_order")
    else:
        put(repo, "app/repo.py", REPO_C2_SUBTLE)
        put(repo, "tests/test_api.py", test_api("[2]", "[1]", "[2, 1]", ""))
        commit(repo, "feat: newest orders first in customer view")


# ---------------------------------------------------------------- c3: export column


def build_c3(repo):
    put(repo, "scripts/export.py", EXPORT_C3)
    commit(repo, "chore: add created_at column and header row to export CSV")


# ---------------------------------------------------------------- assemble


def build(repo, clean):
    git(repo, "checkout", "-q", "-b", "feature/order-pagination")
    build_c1(repo, clean)
    build_c2(repo, clean)
    build_c3(repo)
    git(repo, "checkout", "-q", "main")


def run_tests(repo, ref):
    with tempfile.TemporaryDirectory(prefix="fx-") as tmp:
        wt = pathlib.Path(tmp) / "wt"
        git(repo, "worktree", "add", "-q", "--detach", str(wt), ref)
        try:
            r = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                cwd=wt, capture_output=True, text=True,
            )
            last = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.stdout.strip()
            return r.returncode, last
        finally:
            git(repo, "worktree", "remove", "--force", str(wt))


build_main(CLEAN)
shutil.copytree(CLEAN, SUBTLE)
build(CLEAN, clean=True)
build(SUBTLE, clean=False)

for repo in (CLEAN, SUBTLE):
    for ref in ("main", "feature/order-pagination"):
        rc, last = run_tests(repo, ref)
        print(f"{repo.name:14s} {ref:26s} rc={rc} {last}")
    log = subprocess.run(["git", "log", "--oneline", "feature/order-pagination"], cwd=repo,
                         capture_output=True, text=True).stdout
    stat = subprocess.run(["git", "diff", "--stat", "main...feature/order-pagination"], cwd=repo,
                          capture_output=True, text=True).stdout
    print(log + stat)
