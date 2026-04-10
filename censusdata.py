import requests
import sqlite3
import json
import os
from dotenv import load_dotenv

# get key from .env
load_dotenv()
key = os.getenv("CENSUS_API_KEY")

# build url
base_url = "https://api.census.gov/data/2024/acs/acs5/pums?"
url = base_url + "get=SEX,PWGTP,MAR&SCHL=24&key=" + key

# fetch data
response = requests.get(url)
data = response.json()

# store data in sqlite
# conn = sqlite3.connect("test.db")
# cursor = conn.cursor()

# TODO: create tables if they don't already exist
# ...

# TODO: insert data
# ...

# conn.commit()
# conn.close()