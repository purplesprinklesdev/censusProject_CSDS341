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
    "insertIntoMapping", "resetViews", "bellwetherPuma", "bellwetherState"
}


def get_queries():
    queries = []
    for f in sorted(Path(SQL_DIR).glob("*.sql")):
        if f.stem not in EXCLUDED:
            has_param = "?" in f.read_text(encoding="utf-8")
            queries.append((f.stem, has_param))
    queries.append(("bellwetherPuma", False))
    return queries


def to_label(name):
    return re.sub(r"([A-Z])", r" \1", name).strip().title()


@app.route("/")
def index():
    queries = [(name, to_label(name), has_param) for name, has_param in get_queries()]
    return render_template("index.html", queries=queries)


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

    params = []
    if "?" in query:
        value = request.args.get("value")
        if value is None:
            return jsonify({"error": "This query requires a parameter"}), 400
        try:
            params = [int(value)]
        except ValueError:
            return jsonify({"error": "Parameter must be an integer"}), 400

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
