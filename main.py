#!/usr/bin/env python
import os
import sqlite3
import sys
from configparser import DEFAULTSECT
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
DEFAULT_VINTAGE = "2024"
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
    ------------ Public Use Microdata Bellwether Finder ------------
    Created by Atri Banerjee, Mohit Nair, and Matthew Stall, 2026

    Consult README.md for more general information about the project

    ------------              Command List              ------------
    q                               :   quits the program, or exits subcommand
    quit                            :   quits the program

    pull                            :   pulls data from US Census API
        - all                       :   pull entire US dataset (~50mins)
        - [STATE_NUMBER]            :   pull a specific state (1-2mins)
        - [STATE_ABBREVIATION]      :   pull a specific state (1-2mins)

    bellwether                      :   run the bellwether ranking script
        - puma                      :   rank pumas by distance to dataset mean
        - state                     :   rank states by distance to US mean

    rowsIn [TABLE]                  :   counts the number of rows in [TABLE]. Options:
                                    :   Person, Household, State, PUMA, Race
                                    :   NOTE: for Person and Household, this does not
                                    :   correspond to the number of people or households,
                                    :   use "peopleInData" or "householdsInData" instead

    datapreview [TABLE] [NUMBER]    :   shows the top [NUMBER] of rows in [TABLE]. If
                                    :   number is not supplied then 15 will be used

    help                            :   display this menu

    eligibleVotersByPuma            :   lists the number and percentage of eligible
                                        voters in each puma
    avgAge                          :   computes the average age of people in the dataset
    countUnder [AGE]                :   counts all people under a given age (e.g. "countUnder 20")
    multilingualWorkersNoHIByRace   :   finds multilingual workers with no health insurance
    overcrowdedHouseholds           :   finds crowded households based on household income,
                                    :   the number of dependents, etc.
    pctInsured                      :   outputs the percentage of people with health insurance
    topPumas                        :   determines the most populated PUMAs
    peopleInData                    :   counts the number of people in the dataset
    peopleInState [STATE]           :   counts the number of people in the state (abbreviation)
    peopleInPuma [STATE] [PUMA]     :   counts the number of people in the puma
    householdsInData                :   counts the number of households in the dataset
    householdsInState [STATE]       :   counts the number of households in the state (abbreviation)
    householdsInPuma [STATE] [PUMA] :   counts the number of households in the puma
    pumasInState [STATE]            :   displays all PUMAs and their human-readable names in [STATE]
    """


def buildCensusURL(vars, state, apikey):
    url = CENSUS_BASE_URL + vintage + SURVEY + "?get="
    for var in vars:
        if var[0] == "&":
            url = url[:-1]
        url += var + ","
    url = url[:-1]
    url += "&for=state:" + str(state)
    url += "&key=" + apikey
    return url


def printQueryResult(result):
    columns = [d[0] for d in result.description]

    headers = ""
    for col in columns:
        headers += str(col) + ", "
    headers = headers[: len(headers) - 2]
    print(headers)

    for row in result:
        string = ""
        for element in row:
            string += str(element) + ", "
        string = string[: len(string) - 2]
        print(string)


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
        sys.exit(1)

    conn = sqlite3.connect(DB_FILE, isolation_level="DEFERRED")
    cur = conn.cursor()

    while True:
        print("Fetching Person Data... State " + str(state))
        person_url = buildCensusURL(CENSUS_PERSON_VARIABLES, state, api_key)
        try:
            p_response = requests.get(person_url)

            if p_response.status_code == 200:
                print("Response recieved successfully.")
                break
            elif p_response.status_code == 204:
                print(
                    f"Response code {p_response.status_code} received, state contains no records."
                )
                return
            elif p_response.status_code >= 200 and p_response.status_code < 300:
                print(f"Response code {p_response.status_code} received.")
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
            elif h_response.status_code == 204:
                print(
                    f"Response code {h_response.status_code} received, state contains no records."
                )
                return
            elif h_response.status_code >= 200 and h_response.status_code < 300:
                print(f"Response code {h_response.status_code} received.")
                break
            print(
                f"Response failed with code {h_response.status_code}, retrying in 5 minutes..."
            )
        except ConnectionError:
            print("Response timed out, retrying in 5 minutes...")
        sleep(5 * 60)

    h_data = h_response.json()

    print("Formatting data...")

    # Remove headers
    p_data.pop(0)
    h_data.pop(0)

    p_redundant_index = p_data[0].index("P")
    h_redundant_index = h_data[0].index("H")

    for row_i in range(0, len(p_data)):
        row = p_data[row_i]
        if row[3] == 0:
            p_data.pop(row_i)
            continue
        row.pop(p_redundant_index)
    for row_i in range(0, len(h_data)):
        row = h_data[row_i]
        if row[3] == 0:
            h_data.pop(row_i)
            continue
        row.pop(h_redundant_index)

    try:
        print("Writing Data to Person Table...")
        cur.execute("BEGIN")
        cur.executemany(insert_into_person, p_data)
        conn.commit()
    except sqlite3.Error as er:
        conn.rollback()
        print(
            f"""Database error recieved when inserting Person data on state {state}. Check the error, and consider retrying.
            Error received from SQLite: {er}"""
        )

    try:
        print("Writing Data to Household Table...")
        cur.execute("BEGIN")
        cur.executemany(insert_into_household, h_data)
        conn.commit()
    except sqlite3.Error as er:
        conn.rollback()
        print(
            f"""Database error recieved when inserting Household data on state {state}. Check the error, and consider retrying.
            Error received from SQLite: {er}"""
        )

    conn.close()
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

    dataset_avgs = cur.execute("SELECT * FROM NationalAvg").fetchall()
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


def bellwetherStateQuery(cur):
    raw_wavgs = cur.execute("SELECT * FROM StateProfile")
    raw_wavgs_rows = raw_wavgs.fetchall()
    columns = [d[0] for d in raw_wavgs.description]

    puma_stats = pd.DataFrame(raw_wavgs_rows, columns=columns)
    columns.remove("STATE")
    puma_stats = puma_stats.set_index(["STATE"])
    feature_cols = columns

    # All of this math and statistics heavy stuff was
    # handled mostly by Claude Sonnet 4.6

    X = puma_stats[feature_cols].values

    dataset_avgs = cur.execute("SELECT * FROM NationalAvg").fetchall()
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

conn = sqlite3.connect(DB_FILE, isolation_level=None)
cur = conn.cursor()

vintage = DEFAULT_VINTAGE

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
        bellwether_state = Path(SQL_DIR + "bellwetherState.sql").read_text(
            encoding="utf-8"
        )
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
        cur.executescript(bellwether_state)
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
    print("")
    user_in = input("Enter Command: ")

    user_args = user_in.split()
    if len(user_args) < 1:
        continue
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
                if len(user_args) > 0 and user_args[0].lower() == "puma":
                    try:
                        bellwetherPumaQuery(cur)
                    except sqlite3.Error as er:
                        print(
                            f"A SQL error occured during bellwether calculation.\nError: {er}"
                        )
                    break
                elif len(user_args) > 0 and user_args[0].lower() == "state":
                    try:
                        bellwetherStateQuery(cur)
                    except sqlite3.Error as er:
                        print(
                            f"A SQL error occured during bellwether calculation.\nError: {er}"
                        )
                    break
                else:
                    print(
                        'bellwether - Subcommand options: "puma", "state". See "help" for more info. "q" to exit this submenu'
                    )
                    subcommand_args = input("\nEnter Subcommand: ").split()
                    if (
                        subcommand_args[0].lower() == "q"
                        or subcommand_args[0].lower() == "quit"
                    ):
                        break
                    if subcommand_args[0].lower() == "help":
                        print(helpMenu())
                        continue
                    user_args = subcommand_args
            continue
        case "pull":
            load_dotenv()
            api_key = os.getenv("CENSUS_API_KEY")
            vintage = os.getenv("VINTAGE")

            if vintage is None:
                vintage = DEFAULT_VINTAGE

            if api_key is None:
                print("API Key missing!")
                conn.close()
                sys.exit(1)

            while True:
                if len(user_args) > 0 and user_args[0].lower() == "all":
                    query = "SELECT State FROM State"
                    res = cur.execute(query).fetchall()
                    conn.close()
                    print("This may take a while...")
                    for row in res:
                        populateTables(row[0], api_key)
                    break
                elif len(user_args) > 0 and user_args[0].isnumeric():
                    conn.close()
                    populateTables(user_args[0], api_key)
                    break
                elif len(user_args[0]) == 2:
                    query = "SELECT State FROM State WHERE abbrev=?"
                    res = cur.execute(query, (user_args[0],)).fetchall()
                    conn.close()
                    for row in res:
                        populateTables(row[0], api_key)
                    break
                else:
                    print(
                        'pull - Subcommand options: "all", "[STATE_NUMBER]", "[STATE_ABBREVIATION]". See "help" for more info. "q" to exit this submenu'
                    )
                    subcommand_args = input("\nEnter Subcommand: ").split()
                    if (
                        subcommand_args[0].lower() == "q"
                        or subcommand_args[0].lower() == "quit"
                    ):
                        break
                    if subcommand_args[0].lower() == "help":
                        print(helpMenu())
                        continue
                    user_args = subcommand_args
            conn = sqlite3.connect(DB_FILE, isolation_level=None)
            cur = conn.cursor()
            continue
        case "rowsin":
            query = "SELECT COUNT(*) AS Rows FROM"
            while True:
                if len(user_args) < 1:
                    print(
                        'rowsIn - Subcommand options: "[TABLE]". See "help" for more info. "q" to exit this submenu'
                    )
                    subcommand_args = input("\nEnter Subcommand: ").split()
                    if (
                        subcommand_args[0].lower() == "q"
                        or subcommand_args[0].lower() == "quit"
                    ):
                        break
                    if subcommand_args[0].lower() == "help":
                        print(helpMenu())
                        continue
                    user_args = subcommand_args
                    continue
                match user_args[0].lower():
                    case "person":
                        query += " Person;"
                        break
                    case "household":
                        query += " Household;"
                        break
                    case "state":
                        query += " State;"
                        break
                    case "puma":
                        query += " PUMA;"
                        break
                    case "race":
                        query += " Race;"
                        break
                    case _:
                        print(
                            'rowsIn - Subcommand options: "[TABLE]". See "help" for more info. "q" to exit this submenu'
                        )
                        subcommand_args = input("\nEnter Subcommand: ").split()
                        if (
                            subcommand_args[0].lower() == "q"
                            or subcommand_args[0].lower() == "quit"
                        ):
                            break
                        if subcommand_args[0].lower() == "help":
                            print(helpMenu())
                            continue
                        user_args = subcommand_args
                        continue
            printQueryResult(cur.execute(query))
            continue
        case "datapreview":
            query = "SELECT * FROM "
            while True:
                if len(user_args) < 1:
                    print(
                        'dataPreview - Subcommand options: "[TABLE]", [NUMBER]. Number is optional. See "help" for more info. "q" to exit this submenu'
                    )
                    subcommand_args = input("\nEnter Subcommand: ").split()
                    if (
                        subcommand_args[0].lower() == "q"
                        or subcommand_args[0].lower() == "quit"
                    ):
                        break
                    if subcommand_args[0].lower() == "help":
                        print(helpMenu())
                        continue
                    user_args = subcommand_args
                    continue
                match user_args[0].lower():
                    case "person":
                        query += "Person"
                        break
                    case "household":
                        query += "Household"
                        break
                    case "state":
                        query += "State"
                        break
                    case "puma":
                        query += "PUMA"
                        break
                    case "race":
                        query += "Race"
                        break
                    case _:
                        print(
                            'dataPreview - Subcommand options: "[TABLE]", [NUMBER]. Number is optional. See "help" for more info. "q" to exit this submenu'
                        )
                        subcommand_args = input("\nEnter Subcommand: ").split()
                        if subcommand_args[0] == "q":
                            break
                        if subcommand_args[0] == "help":
                            print(helpMenu())
                            continue
                        user_args = subcommand_args
                        continue
            if len(user_args) < 2 or not user_args[1].isnumeric():
                query += " LIMIT 15;"
                printQueryResult(cur.execute(query))
            else:
                query += " LIMIT ?;"
                printQueryResult(cur.execute(query, (user_args[1],)))
            continue

    command_blocklist = [
        "createTables",
        "bellwetherPuma",
        "bellwetherState",
        "insertIntoMapping",
        "insertIntoPuma",
        "nationalAvg",
    ]
    if any(user_command in s for s in command_blocklist):
        print(f'Invalid command: {user_command} See "help" for a full list.')
        continue

    try:
        query = Path(SQL_DIR + user_command + ".sql").read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f'Invalid command: {user_command} See "help" for a full list.')
        continue

    param_count = query.count("?")
    while len(user_args) < param_count:
        print("Command is missing arguments. Please provide them in your subcommand.")
        help = helpMenu()
        start = help.find(user_command)
        if start != -1:
            end = help.find("\n", start)
            command_help = help[start:end]
            print(command_help)
        subcommand_args = input("\nEnter Subcommand: ").split()
        if subcommand_args[0].lower() == "q" or subcommand_args[0].lower() == "quit":
            break
        if subcommand_args[0].lower() == "help":
            print(helpMenu())
            continue
        user_args = subcommand_args
    if len(user_args) < param_count:
        continue

    # trim off extra args not supported by the query
    user_args = user_args[:param_count]

    # Run SQL
    try:
        if len(user_args) < 1:
            result = cur.execute(query)
        else:
            result = cur.execute(query, user_args)
        printQueryResult(result)
    except sqlite3.Error as er:
        print(f"An error occured in SQLite when running the command.\n Error: {er}")
