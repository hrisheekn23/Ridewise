import os
import re
import sqlite3

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|reindex|"
    r"begin|commit|rollback|savepoint|release|grant|revoke)\b",
    re.IGNORECASE,
)

def _connect(db_path):
    if not os.path.isfile(db_path):
        raise FileNotFoundError(
            f"Database not found: {db_path}. Put ridewise.db in the project folder "
            "or set RIDEWISE_DB_PATH in .env."
        )
    uri = "file:" + os.path.abspath(db_path).replace("\\", "/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.set_authorizer(_authorizer)
    return conn

def _authorizer(action, arg1, arg2, db_name, trigger_name):
    # SQLite-level defense: permit read-only SELECT operations only.
    allowed = {
        sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    }
    return sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY

def get_schema(db_path="ridewise.db"):
    conn = _connect(db_path)
    try:
        tables = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()
        parts = []
        for table in tables:
            parts.append(f"TABLE {table['name']}: {table['sql']}")
        return "\n".join(parts)
    finally:
        conn.close()

def _contains_customer_scope(sql, customer_id):
    # Conservative check: reject customer queries unless the SQL explicitly filters
    # a customer_id column to this session's exact ID. Parameterized form is supported
    # only when the ID is supplied as the first parameter by this module.
    normalized = re.sub(r"\s+", " ", sql).lower()
    cid = customer_id.lower().replace("'", "''")
    literal_patterns = [
        rf"\bcustomer_id\s*=\s*'{re.escape(cid)}'",
        rf"\bcustomer_id\s*=\s*\"{re.escape(customer_id.lower())}\"",
    ]
    if any(re.search(p, normalized, re.I) for p in literal_patterns):
        return sql, ()
    if re.search(r"\bcustomer_id\s*=\s*\?", normalized):
        return sql, (customer_id,)
    raise PermissionError(
        "Customer-mode query must explicitly filter customer_id to the signed-in session's ID."
    )

def run_readonly_query(sql, db_path="ridewise.db", role="Customer", customer_id=None):
    if not sql or not isinstance(sql, str):
        return []
    cleaned = sql.strip().rstrip(";")
    if not re.match(r"^(select|with)\b", cleaned, re.IGNORECASE):
        raise PermissionError("Only SELECT queries are allowed.")
    if ";" in cleaned or "--" in cleaned or "/*" in cleaned or FORBIDDEN.search(cleaned):
        raise PermissionError("Query contains a blocked statement or comment.")
    params = ()
    if role == "Customer":
        if not customer_id:
            raise PermissionError("A customer ID is required.")
        cleaned, params = _contains_customer_scope(cleaned, customer_id)
    conn = _connect(db_path)
    try:
        cursor = conn.execute(cleaned, params)
        return [dict(row) for row in cursor.fetchmany(100)]
    finally:
        conn.close()
