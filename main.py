#!/usr/bin/env python
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from scipy.spatial.distance import mahalanobis
from scipy.stats import chi2
from sklearn.covariance import MinCovDet

CENSUS_BASE_URL = "https://api.census.gov/data/"
VINTAGE = "2024"
SURVEY = "/acs/acs5/pums"

CENSUS_PERSON_VARIABLES = [
    "SERIALNO",
    "SPORDER",
    "PUMA",
    "PWGTP",
    "SEX",
    "RAC1P",
    "HISP",
    "AGEP",
    "SCHL",
    "MAR",
    "ESR",
    "&STATE=39",  # just test ohio for now
]
CENSUS_HOUSEHOLD_VARIABLES = [
    "SERIALNO",
    "PUMA",
    "WGTP",
    "HINCP",
    "VALP",
    "HUPAC",
    "GRPIP",
    "TAXAMT",
    "&STATE=39",  # just test ohio for now
]

DB_FILE = "db.db"
COMMAND_FILE_PATH = "commands.txt"

SQL_DIR = "sql/"


def buildCensusURL(vars, apikey):
    url = CENSUS_BASE_URL + VINTAGE + SURVEY + "?get="
    for var in vars:
        if var[0] == "&":
            url = url[:-1]
        url += var + ","
    url = url[:-1]
    url += "&key=" + apikey
    return url


def bellwetherPumaQuery(cur):
    # exactly what this will end up looking like is tbd
    """
    try:
        personQuery = Path(SQL_DIR + "bellwetherPumaPerson.sql").read_text(
            encoding="utf-8"
        )
        householdQuery = Path(SQL_DIR + "bellwetherPumaHousehold.sql").read_text(
            encoding="utf-8"
        )
    except FileNotFoundError:
        print("Missing Critical SQL files.")
        return

    personRes = cur.execute(personQuery)
    householdRes = cur.execute(householdQuery)
    """
    # change to the materialized view table
    raw_wavgs = cur.execute("SELECT * FROM [materialized view]")
    raw_wavgs_rows = raw_wavgs.fetchall()
    columns = [d[0] for d in raw_wavgs.description]

    puma_stats = pd.DataFrame(raw_wavgs_rows, columns=columns)
    columns.remove("PUMA")
    puma_stats = puma_stats.set_index("PUMA")
    feature_cols = columns

    # Slice only the feature columns for all matrix operations
    X = puma_stats[feature_cols].values

    national_vec = puma_stats[feature_cols].mean().values

    robust_cov = MinCovDet(random_state=42).fit(X)
    inv_cov = robust_cov.get_precision()  # inverse covariance matrix

    distances = [mahalanobis(row, national_vec, inv_cov) for row in X]

    puma_stats["mahal_dist"] = distances
    puma_stats["p_value"] = 1 - chi2.cdf(
        puma_stats["mahal_dist"] ** 2, df=len(feature_cols)
    )

    bellwether_ranking = puma_stats[["mahal_dist", "p_value"]].sort_values("mahal_dist")
    print(bellwether_ranking.head(10))


# --SETUP--
first_run = not os.path.isfile(DB_FILE)

conn = sqlite3.connect(DB_FILE, autocommit=True)
cur = conn.cursor()


if first_run:
    # --Create Tables--
    try:
        create_tables_query = Path(SQL_DIR + "createTables.sql").read_text(
            encoding="utf-8"
        )
        insert_into_person = Path(SQL_DIR + "insertIntoPerson.sql").read_text(
            encoding="utf-8"
        )
    except FileNotFoundError:
        print("Missing SQL files. Please redownload the repo.")
        conn.close()
        sys.exit(1)

    cur.executescript(create_tables_query)

    # --Access Census Data--
    print(
        "Database File does not exist, attempting to pull data from api.census.gov..."
    )

    load_dotenv()
    api_key = os.getenv("CENSUS_API_KEY")

    if api_key is None:
        print("API Key missing!")
        conn.close()
        sys.exit(1)

    # fetch data
    # TODO: for household as well
    person_url = buildCensusURL(CENSUS_PERSON_VARIABLES, api_key)
    response = requests.get(person_url)
    data = response.json()

    print("Response received. Writing to database file...")

    data.pop(0)  # remove headers
    cur.executemany(insert_into_person, data)

    print("Successfully wrote to database")

print("Public Use Microdata Bellwether Finder")
while True:
    # Read user input, process args
    user_in = input("Enter Command: ")

    user_args = user_in.split()
    user_command = user_args[0]
    user_args.pop(0)

    if user_command.lower() == "q" or user_command.lower() == "quit":
        conn.close()
        break

    if user_command.lower() == "bellwether":
        if user_args[0].lower() == "puma":
            bellwetherPumaQuery(cur)
        # else if uArgs[0].lower() == "state":
        # bellwetherPumaQuery(cur)
        else:
            print('Invalid subcommand. Options are "puma" or "state"')
        continue

    try:
        query = Path(SQL_DIR + user_command + ".sql").read_text(encoding="utf-8")
    except FileNotFoundError:
        print("Invalid command: " + user_command)
        continue

    user_args = user_args[: query.count("?")]

    # Run SQL
    if len(user_args) < 1:
        result = cur.execute(query)
    else:
        result = cur.execute(query, user_args)

    for row in result:
        string = ""
        for element in row:
            string += str(element) + ", "
        print(string)
