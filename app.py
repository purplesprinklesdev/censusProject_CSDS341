#!/usr/bin/env python
import re
import sqlite3
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request
from scipy.spatial.distance import mahalanobis
from scipy.stats import chi2
from sklearn.covariance import LedoitWolf
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

DB_FILE = "db.db"
SQL_DIR = "sql/"

EXCLUDED = {
    "createTables", "insertIntoPerson", "insertIntoHousehold",
    "insertIntoMapping", "resetViews", "bellwetherPuma", "bellwetherState",
    "insertIntoPuma",
}

# Queries whose SQL files are CREATE VIEW statements rather than SELECT statements.
# The route will create the view (idempotently) then SELECT from it.
VIEW_QUERIES = {"nationalAvg"}

# Explicit param definitions for queries that take user input.
# Queries not listed here are run with no params.
QUERY_PARAMS = {
    "countUnder":        [{"label": "Age (0–100)",     "type": "number", "min": "0", "max": "100"}],
    "householdsInState": [{"label": "State (e.g. OH)", "type": "text"}],
    "householdsInPuma":  [{"label": "State (e.g. OH)", "type": "text"},
                          {"label": "PUMA #",           "type": "number", "min": "0"}],
    "peopleInState":     [{"label": "State (e.g. OH)", "type": "text"}],
    "peopleInPuma":      [{"label": "State (e.g. OH)", "type": "text"},
                          {"label": "PUMA #",           "type": "number", "min": "0"}],
    "pumasInState":      [{"label": "State (e.g. OH)", "type": "text"}],
    # stateAvg has two identical ? placeholders (person state + household state).
    # We show one input and duplicate the resolved value server-side.
    "stateAvg":          [{"label": "State (e.g. OH)", "type": "text"}],
}


def get_queries():
    queries = []
    for f in sorted(Path(SQL_DIR).glob("*.sql")):
        if f.stem not in EXCLUDED:
            queries.append((f.stem, QUERY_PARAMS.get(f.stem)))
    queries.append(("bellwetherPuma", None))
    return queries


def to_label(name):
    return re.sub(r"([A-Z])", r" \1", name).strip().title()


@app.route("/")
def index():
    queries = [(name, to_label(name), params) for name, params in get_queries()]
    return render_template("index.html", queries=queries)


def _run_view_query(query):
    """Execute a CREATE VIEW file: create view (IF NOT EXISTS), then SELECT from it."""
    m = re.search(r"CREATE\s+VIEW\s+(\w+)", query, re.IGNORECASE)
    if not m:
        return jsonify({"error": "Could not parse view name"}), 500
    view_name = m.group(1)
    create_sql = re.sub(
        r"CREATE\s+VIEW\s+(?!IF\s+NOT\s+EXISTS\s)",
        "CREATE VIEW IF NOT EXISTS ",
        query, count=1, flags=re.IGNORECASE,
    )
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute(create_sql)
        result = cur.execute(f"SELECT * FROM [{view_name}]")
        rows = result.fetchall()
        columns = [d[0] for d in result.description] if result.description else []
        conn.close()
        return jsonify({"columns": columns, "rows": rows})
    except sqlite3.OperationalError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/run/bellwetherPuma")
def run_bellwether_puma():
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        result = cur.execute("SELECT * FROM PumaProfile")
        rows = result.fetchall()
        all_columns = [d[0] for d in result.description]
        conn.close()
    except sqlite3.OperationalError as e:
        return jsonify({"error": str(e)}), 500

    if not rows:
        return jsonify({"columns": [], "rows": []})

    df = pd.DataFrame(rows, columns=all_columns)
    id_cols = ["STATE", "PUMA", "Puma_Name"]
    feature_cols = [c for c in all_columns if c not in id_cols]
    df = df.dropna(subset=feature_cols)

    X = df[feature_cols].values.astype(float)
    national_vec = X.mean(axis=0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    national_scaled = scaler.transform(national_vec.reshape(1, -1))

    lw_cov = LedoitWolf().fit(X_scaled)
    inv_cov = lw_cov.get_precision()
    distances = [mahalanobis(row, national_scaled[0], inv_cov) for row in X_scaled]

    df["Bellwether Score"] = [round(d, 4) for d in distances]
    df["p_value"] = [round(1 - chi2.cdf(d ** 2, df=len(feature_cols)), 4) for d in distances]

    out = df[["STATE", "PUMA", "Puma_Name", "Bellwether Score", "p_value"]].sort_values("Bellwether Score")
    return jsonify({"columns": list(out.columns), "rows": out.values.tolist()})


@app.route("/run/<command>")
def run_query(command):
    if not re.fullmatch(r"[A-Za-z0-9]+", command):
        return jsonify({"error": "Invalid command name"}), 400

    if command == "bellwetherPuma":
        return run_bellwether_puma()

    sql_path = Path(SQL_DIR + command + ".sql")
    if not sql_path.exists() or command in EXCLUDED:
        return jsonify({"error": "Query not found"}), 404

    query = sql_path.read_text(encoding="utf-8")

    if command in VIEW_QUERIES:
        return _run_view_query(query)

    raw_values = request.args.getlist("value")
    param_defs = QUERY_PARAMS.get(command, [])

    # stateAvg uses two identical integer State placeholders but only one user input.
    if command == "stateAvg":
        if not raw_values:
            return jsonify({"error": "State abbreviation required"}), 400
        abbrev = raw_values[0].strip().upper()
        try:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute("SELECT State FROM State WHERE abbrev = ?", (abbrev,)).fetchone()
            conn.close()
        except sqlite3.OperationalError as e:
            return jsonify({"error": str(e)}), 500
        if not row:
            return jsonify({"error": f"Unknown state abbreviation: {abbrev}"}), 400
        params = [row[0], row[0]]
    elif param_defs:
        if len(raw_values) < len(param_defs):
            return jsonify({"error": "Missing required parameters"}), 400
        params = []
        for val, defn in zip(raw_values, param_defs):
            if defn["type"] == "number":
                try:
                    params.append(int(val))
                except ValueError:
                    return jsonify({"error": f"'{defn['label']}' must be a number"}), 400
            else:
                params.append(val.strip())
    else:
        params = []

    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        result = cur.execute(query, params)
        rows = result.fetchall()
        columns = [d[0] for d in result.description] if result.description else []
        conn.close()
        return jsonify({"columns": columns, "rows": rows})
    except sqlite3.OperationalError as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
