#!/usr/bin/env python
import os
import sqlite3
import sys
from pathlib import Path

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
    "HICOV",
    "ESR",
    "WKWN",
    "LANX",
    "ENG",
    "DECADE",
    "CIT",
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
    "TEN",
    "WIF",
]

DB_FILE = "db.db"
COMMAND_FILE_PATH = "commands.txt"

SQL_DIR = "sql/"


def buildCensusURL(vars, state, apikey):
    url = CENSUS_BASE_URL + VINTAGE + SURVEY + "?get="
    for var in vars:
        if var[0] == "&":
            url = url[:-1]
        url += var + ","
    url = url[:-1]
    url += "&for=state:" + str(state)
    url += "&key=" + apikey
    return url


def populateTables(state, api_key):
    try:
        insert_into_person = Path(SQL_DIR + "insertIntoPerson.sql").read_text(
            encoding="utf-8"
        )
        insert_into_household = Path(SQL_DIR + "insertIntoHousehold.sql").read_text(
            encoding="utf-8"
        )
    except FileNotFoundError:
        print("Missing Critical SQL files. Please redownload the repo.")
        conn.close()
        sys.exit(1)

    print("Fetching Person Data... State " + str(state))
    person_url = buildCensusURL(CENSUS_PERSON_VARIABLES, state, api_key)
    p_response = requests.get(person_url)
    p_data = p_response.json()

    print("Fetching Household Data... State" + str(state))
    household_url = buildCensusURL(CENSUS_HOUSEHOLD_VARIABLES, state, api_key)
    h_response = requests.get(household_url)
    h_data = h_response.json()

    print("Response received. Writing to database file...")

    # remove headers
    p_data.pop(0)
    h_data.pop(0)

    cur.executemany(insert_into_person, p_data)
    cur.executemany(insert_into_household, h_data)

    print("Successfully wrote to database. State " + str(state))


def bellwetherPumaQuery(cur):
    # change to the materialized view table
    raw_wavgs = cur.execute("SELECT * FROM PumaProfile")
    raw_wavgs_rows = raw_wavgs.fetchall()
    columns = [d[0] for d in raw_wavgs.description]

    puma_stats = pd.DataFrame(raw_wavgs_rows, columns=columns)
    columns.remove("PUMA")
    puma_stats = puma_stats.set_index("PUMA")
    feature_cols = columns

    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None
    ):  # more options can be specified also
        print(puma_stats)

    X = puma_stats[feature_cols].values

    national_vec = puma_stats[feature_cols].mean().values

    robust_cov = MinCovDet(random_state=42).fit(X)
    inv_cov = robust_cov.get_precision()

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
    print("Database File does not exist, creating tables.")

    # --Create Tables--
    try:
        create_tables_query = Path(SQL_DIR + "createTables.sql").read_text(
            encoding="utf-8"
        )
        insert_into_mapping = Path(SQL_DIR + "insertIntoMapping.sql").read_text(
            encoding="utf-8"
        )
        bellwether_puma = Path(SQL_DIR + "bellwetherPuma.sql").read_text(
            encoding="utf-8"
        )
        bellwether_state = Path(SQL_DIR + "bellwetherPuma.sql").read_text(
            encoding="utf-8"
        )
    except FileNotFoundError:
        print("Missing SQL files. Please redownload the repo.")
        conn.close()
        sys.exit(1)

    cur.executescript(create_tables_query)
    cur.executescript(insert_into_mapping)
    cur.executescript(bellwether_puma)
    # cur.executescript(bellwether_state)

    print('Pull census data with "pull [STATE ABBREVIATION]" or "pull all".\n')

# Main Execution Loop
print("Public Use Microdata Bellwether Finder")
while True:
    # Read user input, process args
    user_in = input("Enter Command: ")

    user_args = user_in.split()
    user_command = user_args[0]
    user_args.pop(0)

    match user_command.lower():
        case "q":
            conn.close()
            break
        case "quit":
            conn.close()
            break
        case "bellwether":
            if user_args[0].lower() == "puma":
                bellwetherPumaQuery(cur)
            # else if uArgs[0].lower() == "state":
            # bellwetherPumaQuery(cur)
            else:
                print('Invalid subcommand. Options are "puma" or "state"')
            continue
        case "pull":
            print("This may take a while...")
            load_dotenv()
            api_key = os.getenv("CENSUS_API_KEY")

            if api_key is None:
                print("API Key missing!")
                conn.close()
                sys.exit(1)

            if user_args[0].lower() == "all":
                query = "SELECT State FROM State"
                res = cur.execute(query)
                for row in res:
                    populateTables(row[0], api_key)
            else:
                query = "SELECT State FROM State WHERE abbrev=?"
                print(user_args[0])
                res = cur.execute(query, (user_args[0],))
                for row in res:
                    populateTables(row[0], api_key)
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
