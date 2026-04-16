#!/usr/bin/env python
import os
import sqlite3
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

CENSUS_BASE_URL = "https://api.census.gov/data/"
VINTAGE = "2024"
SURVEY = "/acs/acs5/pums"

CENSUS_VARIABLES = [
    "SERIALNO",
    "SPORDER",
    "PWGTP",
    "PUMA",
    "SEX",
    "MAR",
    "SCHL",
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


# --SETUP--
firstRun = not os.path.isfile(DB_FILE)

conn = sqlite3.connect(DB_FILE, autocommit=True)
cur = conn.cursor()


if firstRun:
    # --Create Tables--
    try:
        createTablesQuery = Path(SQL_DIR + "createTables.sql").read_text(
            encoding="utf-8"
        )
        insertIntoPerson = Path(SQL_DIR + "insertIntoPerson.sql").read_text(
            encoding="utf-8"
        )
    except FileNotFoundError:
        print("Missing SQL files. Please redownload the repo.")
        conn.close()
        sys.exit(1)

    cur.executescript(createTablesQuery)

    # --Access Census Data--
    print(
        "Database File does not exist, attempting to pull data from api.census.gov..."
    )

    load_dotenv()
    apiKey = os.getenv("CENSUS_API_KEY")

    if apiKey is None:
        print("API Key missing!")
        conn.close()
        sys.exit(1)

    # fetch data
    # TODO: for household as well
    personurl = buildCensusURL(CENSUS_VARIABLES, apiKey)
    response = requests.get(personurl)
    data = response.json()

    print("Response received. Writing to database file...")

    data.pop(0)  # remove headers
    cur.executemany(insertIntoPerson, data)

    print("Successfully wrote to database")

print("Public Use Microdata Bellwether Finder")
while True:
    # Read user input, process args
    uIn = input("Enter Command: ")

    uArgs = uIn.split()
    ucommand = uArgs[0]
    uArgs.pop(0)

    if ucommand.lower() == "q" or ucommand.lower() == "quit":
        conn.close()
        break

    try:
        query = Path(SQL_DIR + ucommand + ".sql").read_text(encoding="utf-8")
    except FileNotFoundError:
        print("Invalid command: " + ucommand)
        continue

    uArgs = uArgs[: query.count("?")]

    # Run SQL
    if len(uArgs) < 1:
        result = cur.execute(query)
    else:
        result = cur.execute(query, uArgs)

    for row in result:
        string = ""
        for element in row:
            string += str(element) + ", "
        print(string)
