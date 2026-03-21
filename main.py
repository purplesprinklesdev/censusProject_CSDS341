#!/usr/bin/env python

import sqlite3
from pathlib import Path

DB_PATH = "db/test.db"
COMMAND_FILE_PATH = "commands.txt"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Parse Command File

fp = Path(COMMAND_FILE_PATH)

try:
    lines = fp.read_text(encoding="utf-8").splitlines()
except FileNotFoundError:
    print("Create the Command file, commands.txt")
    exit()

commands = {}

for line in lines:
    splitStr = line.split("=")
    commands[splitStr[0]] = splitStr[1]

while True:
    # Read user input, process args
    uIn = input("Enter Command: ")

    uArgs = uIn.split()
    ucommand = uArgs[0]

    if ucommand[0].lower() == "q":
        break

    uArgs.pop(0)

    query = commands[ucommand]

    # Fill args into query
    for i in range(len(query)):
        if query[i] == "$" and query[i - 1] != "\\":
            num = query[i + 1 :].split(" ")[0]
            if num.isdigit():
                query = query[:i] + uArgs[int(num)] + query[i + len(num) + 1 :]

    # Run SQL
    cur.execute(query)
