# Analyzing Census Data to Find Bellwether PUMAs

## Background
A Bellwether county is a county that is representative of how a state or the whole country might vote in elections. They are strong predictors of election outcomes, and thus important information for pollsters and politicians.

A PUMA (Public Use Microdata Area) is the smallest geographic distinction in the US Census. PUMAs are roughly on the same scale as counties, though some PUMAs may contain multiple counties while others may be smaller than a county.

## Instructions

- Clone the repo

- Ensure python and pip are intalled AND on your PATH

- `pip install -r requirements.txt`

- `python main.py`

You should now see a prompt that says `Enter Command:`. Try "countUnder 20", and check that you get a realistic value for your dataset.

## List of SQL Commands
- avgAge: computes the average age of people in the dataset
- bellwetherPuma: ranks bellwether PUMAs of the downloaded dataset
- bellwetherState: ranks bellwether states
- countUnder: counts all people under a given age (e.g. "countUnder 20")
- eligibleVotersByPuma: counts citizens over the age of 18
- multilingualWorkersNoHIByRace: finds multilingual workers with no health insurance
- overcrowdedHouseholds: finds crowded households based on household income, the number of dependents, etc.
- pctInsured: outputs the percentage of people with health insurance
- topPumas: determines the most populated PUMAs

