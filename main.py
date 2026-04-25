#!/usr/bin/env python
import os
import sqlite3
import sys
from pathlib import Path
from time import sleep

import pandas as pd
import requests
from dotenv import load_dotenv

# The following imports are our statistics libraries
# for calculating bellwethers
from scipy.spatial.distance import mahalanobis
from scipy.stats import chi2
from sklearn.covariance import LedoitWolf
from sklearn.preprocessing import StandardScaler

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
    "&RT=P",
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
    "&RT=H",
]

DB_FILE = "db.db"
COMMAND_FILE_PATH = "commands.txt"
SQL_DIR = "sql/"


def helpMenu():
    return """
    Public Use Microdata Bellwether Finder
    Created by Atri Banerjee, Mohit Nair, and Matthew Stall, 2026

    - Command List -
    q                               :   quits the program, or exits subcommand
    quit                            :   quits the program

    pull                            :   pulls data from US Census API
        - all                       :   pull entire US dataset (many hours)
        - [STATE_NUMBER]            :   pull a specific state (~15-20mins)
        - [STATE_ABBREVIATION]      :   pull a specific state (~15-20mins)

    bellwether                      :   run the bellwether ranking script
        - puma                      :   rank pumas by distance to dataset mean
        - state                     :   rank states by distance to US mean

    help                            :   display this menu

    eligibleVotersByPuma            :   lists the number and percentage of eligible
                                        voters in each puma
    avgAge                          :   computes the average age of people in the dataset
    countUnder [AGE]                :   counts all people under a given age (e.g. "countUnder 20")
    multilingualWorkersNoHIByRace   :   finds multilingual workers with no health insurance
    overcrowdedHouseholds           :   finds crowded households based on household income, the number of dependents, etc.
    pctInsured                      :   outputs the percentage of people with health insurance
    topPumas                        :   determines the most populated PUMAs
    """


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


def trimInput(data, redundant_indices):
    for row in data:
        yield tuple(val for i, val in enumerate(row) if i not in redundant_indices)


def populateTables(state, api_key):
    print("This may take a while...")
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

    while True:
        print("Fetching Person Data... State " + str(state))
        person_url = buildCensusURL(CENSUS_PERSON_VARIABLES, state, api_key)
        try:
            p_response = requests.get(person_url)

            if p_response.status_code == 200:
                print("Response recieved successfully.")
                break
            print(
                f"Response failed with code {p_response.status_code}, retrying in 5 minutes..."
            )
        except ConnectionError:
            print("Response timed out, retrying in 5 minutes...")
        sleep(5 * 60)

    p_data = p_response.json()

    while True:
        print("Fetching Household Data... State " + str(state))
        household_url = buildCensusURL(CENSUS_HOUSEHOLD_VARIABLES, state, api_key)
        try:
            h_response = requests.get(household_url)

            if h_response.status_code == 200:
                print("Response recieved successfully.")
                break
            print(
                f"Response failed with code {h_response.status_code}, retrying in 5 minutes..."
            )
        except ConnectionError:
            print("Response timed out, retrying in 5 minutes...")
        sleep(5 * 60)

    h_data = h_response.json()

    print("Writing results from API to database file...")

    try:
        cur.executemany(insert_into_person, trimInput(p_data, {0, p_data.index("P")}))
        cur.executemany(
            insert_into_household, trimInput(h_data, {0, h_data.index("H")})
        )
    except sqlite3.Error as er:
        print(
            f"Database error recieved when inserting data on state {state}. Check the error, and consider retrying."
        )
        print(f"Error received from SQLite: {er}")

    print(f"Successfully wrote to database. State {state}")


def bellwetherPumaQuery(cur):
    raw_wavgs = cur.execute("SELECT * FROM PumaProfile")
    raw_wavgs_rows = raw_wavgs.fetchall()
    columns = [d[0] for d in raw_wavgs.description]

    puma_stats = pd.DataFrame(raw_wavgs_rows, columns=columns)
    columns.remove("STATE")
    columns.remove("PUMA")
    columns.remove("Puma_Name")
    puma_stats = puma_stats.set_index(["STATE", "PUMA", "Puma_Name"])
    feature_cols = columns

    # All of this math and statistics heavy stuff was
    # handled mostly by Claude Sonnet 4.6

    X = puma_stats[feature_cols].values

    dataset_avgs = cur.execute("SELECT * FROM DatasetAvg").fetchall()
    col_names = [d[0] for d in cur.description]
    national_df = pd.DataFrame(dataset_avgs, columns=col_names)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    national_scaled = scaler.transform(national_df[feature_cols].values)

    # LedoitWolf handles near-singular matrices via shrinkage
    lw_cov = LedoitWolf().fit(X_scaled)
    inv_cov = lw_cov.get_precision()

    # Compute distances
    distances = [mahalanobis(row, national_scaled[0], inv_cov) for row in X_scaled]

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
    print("Database file does not exist yet. Creating tables...")

    # --Create Tables and Views--
    try:
        create_tables_query = Path(SQL_DIR + "createTables.sql").read_text(
            encoding="utf-8"
        )
        insert_into_mapping = Path(SQL_DIR + "insertIntoMapping.sql").read_text(
            encoding="utf-8"
        )
        insert_into_puma = Path(SQL_DIR + "insertIntoPuma.sql").read_text(
            encoding="utf-8"
        )
        bellwether_puma_view = Path(SQL_DIR + "bellwetherPuma.sql").read_text(
            encoding="utf-8"
        )
        """bellwether_state = Path(SQL_DIR + "bellwetherPuma.sql").read_text(
            encoding="utf-8"
        )"""
        national_avg_view = Path(SQL_DIR + "nationalAvg.sql").read_text(
            encoding="utf-8"
        )
    except FileNotFoundError:
        print("Missing SQL files. Please redownload the repo.")
        conn.close()
        sys.exit(1)

    try:
        cur.executescript(create_tables_query)
        cur.executescript(insert_into_mapping)
        cur.executescript(insert_into_puma)
        cur.executescript(bellwether_puma_view)
        # cur.executescript(bellwether_state)
        cur.executescript(national_avg_view)
    except sqlite3.Error as e:
        print(f"SQL error during setup: {e}")
        conn.close()
        sys.exit(1)

    print("Tables created. Populate tables using the pull command as follows: ")
    print('Pull census data with "pull [STATE ABBREVIATION]" or "pull all".')
    print('e.g. "pull OH"\n')

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
        case "help":
            print(helpMenu())
            continue
        case "bellwether":
            while True:
                if user_args[0].lower() == "puma":
                    try:
                        bellwetherPumaQuery(cur)
                    except sqlite3.Error as er:
                        print(
                            f"A SQL error occured during bellwether calculation.\nError: {er}"
                        )
                    break
                # else if uArgs[0].lower() == "state":
                # bellwetherPumaQuery(cur)
                else:
                    print(
                        'bellwether - Subcommand options: "puma", "state". See "help" for more info. "q" to exit this submenu'
                    )
                    subcommand_args = input("Enter Subcommand: ").split()
                    if subcommand_args[0] == "q":
                        break
                    if subcommand_args[0] == "help":
                        print(helpMenu())
                        continue
                    user_args = subcommand_args
            continue
        case "pull":
            load_dotenv()
            api_key = os.getenv("CENSUS_API_KEY")

            if api_key is None:
                print("API Key missing!")
                conn.close()
                sys.exit(1)
            while True:
                if user_args[0].lower() == "all":
                    query = "SELECT State FROM State"
                    res = cur.execute(query).fetchall()
                    for row in res:
                        populateTables(row[0], api_key)
                    break
                elif user_args[0].isnumeric():
                    populateTables(user_args[0], api_key)
                    break
                elif len(user_args[0]) == 2:
                    query = "SELECT State FROM State WHERE abbrev=?"
                    res = cur.execute(query, (user_args[0],))
                    for row in res:
                        populateTables(row[0], api_key)
                    break
                else:
                    print(
                        'pull - Subcommand options: "all", "[STATE_NUMBER]", "[STATE_ABBREVIATION]". See "help" for more info. "q" to exit this submenu'
                    )
                    subcommand_args = input("Enter Subcommand: ").split()
                    if subcommand_args[0] == "q":
                        break
                    if subcommand_args[0] == "help":
                        print(helpMenu())
                        continue
                    user_args = subcommand_args
            continue

    try:
        query = Path(SQL_DIR + user_command + ".sql").read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f'Invalid command: {user_command} See "help" for a full list.')
        continue

    # TODO: subcommand stuff for arbitrary SQL command

    # trim off extra args not supported by the query
    user_args = user_args[: query.count("?")]

    # Run SQL
    try:
        if len(user_args) < 1:
            result = cur.execute(query)
        else:
            result = cur.execute(query, user_args)

        columns = [d[0] for d in result.description]

        headers = ""
        for col in columns:
            headers += str(col) + ", "
        headers = headers[: len(headers) - 1]
        print(headers)

        for row in result:
            string = ""
            for element in row:
                string += str(element) + ", "
            string = string[: len(string) - 1]
            print(string)
    except sqlite3.Error as er:
        print(f"An error occured in SQLite when running the command.\n Error: {er}")
