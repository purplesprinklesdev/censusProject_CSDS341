# Analyzing Census Data to Find Bellwether PUMAs

Created by Atri Banerjee, Mohit Nair and Matthew Stall

This project uses [Public Use Microdata Samples](https://www.census.gov/programs-surveys/acs/microdata.html) from the United States Census to estimate areas of the country that might be "bellwethers." A bellwether is a small area that is electorally representative of a much larger area that it resides in. Usually the term bellwether is used to describe counties that predict presidential election results. If a bellwether is found, it can be a strong predictor of election outcomes, and thus polling and tracking bellwethers is an important task for pollsters, political parties and election researchers. Specifically, our project finds bellwether PUMAs, (Public Use Microdata Areas) which are roughly county sized. PUMS data lacks granularity on the county level for privacy reasons, but PUMAs are a decent approximation.

The program calculates bellwether PUMAs by tracking 20 demographic, economic, and educational variables and finding the PUMAs which minimize the Mahalanobis distance between their mean and the national mean. In a sense, we are finding the "most average" places in the U.S. The key limitation with our findings is the small number of variables being tracked. The computational complexity scales dramatically as variables are added, but 20 is not nearly enough to get accurate estimates of bellwethers. We are also assuming that these variables we are tracking will correlate in some way with voting tendencies. Some variables may do this more than others, and not accounting for that is another serious limitation with our findings. Future developments towards this goal could improve on our work by increasing variable size (potentially choosing variables more strategically) and integrating data on how much a given variable predicts voter tendency.

Additionally, this project is capable of querying the PUMS for other data that might be useful for these groups. Things like the number of eligible voters in each PUMA will help in interpreting bellwether data. See the [Command List](#command-list) for more on this.

## Installation Instructions

Tested and working on NixOS, MacOS, and Windows 11. 

#### NixOS

- Clone the repo

- Run `nix develop`,

- `python -m venv .venv`,

- `pip install -r requirements.txt`

- `./main.py` to start the CLI

- You should now see a prompt that says `Enter Command:`
  
- Type "q" and hit enter to quit, and next you should get an API key set up

#### Windows, MacOS, Other Linux Distros

- Ensure `python` and `pip` are installed AND on your PATH

- Clone the repo

- Navigate to the repo directory in your terminal of choice, and run `pip install -r requirements.txt`

- Run `python main.py` to start the CLI

- You should now see a prompt that says `Enter Command:`

- Type "q" and hit enter to quit, and next you should get an API key set up

## Add API Key

First you'll need to make the `.env` file and put your API Key in it. You can get a census API key for free from the [Census Bureau Website](https://api.census.gov/data/key_signup.html)

Your `.env` should look like this: `CENSUS_API_KEY=YOUR_KEY_GOES_HERE`

If you want to use data from a year other than 2024, (the default) you can add `VINTAGE=2022` for example.

## Using the CLI

You should get started by pulling census data. You can pull a state, which takes about 1-2 mins, with `pull OH` (to get Ohio). You can get all U.S. data with `pull all`, though this can take about an hour.

Once you have pulled data successfully, you can execute various queries on it. Try "countUnder 200", and check that you get a realistic value for your dataset. (It should be your region's population)

## Using the Web UI

Once commands in the CLI are working, try out the web UI!

`python app.py` starts up the server. You should see a link to a locally-hosted frontend.

## Command List

- `q` - quits the program, or exits subcommand
- `quit` - quits the program

- `pull` - pulls data from US Census API
    - `all` - pull entire US dataset (~50mins)
    - `[STATE_NUMBER]` - pull a specific state (1-2mins)
    - `[STATE_ABBREVIATION]` - pull a specific state (1-2mins)

- `bellwether` - run the bellwether ranking script
    - `puma` - rank pumas by distance to dataset mean
    - `state` - rank states by distance to US mean
    - `pumaInState [STATE]` - rank pumas by distance to [STATE] mean
- `rowsIn [TABLE]` - counts the number of rows in [TABLE]. Options: Person, Household, State, PUMA, Race. NOTE: for Person and Household, this does not correspond to the number of people or households, use "peopleInData" or "householdsInData" instead
- `datapreview [TABLE] [NUMBER]` - shows the first [NUMBER] rows in [TABLE]. If number is not supplied then 15 will be used
- `help` - display this menu
- `eligibleVotersByPuma` - lists the number and percentage of eligible voters in each puma
- `avgAge` - computes the average age of people in the dataset
- `countUnder [AGE]` - counts all people under a given age (e.g. "countUnder 20")
- `multilingualWorkersNoHIByRace` - finds multilingual workers with no health insurance
- `overcrowdedHouseholds` - finds crowded households based on household income, the number of dependents, etc.
- `pctInsured` - outputs the percentage of people with health insurance
- `topPumas` - determines the most populated PUMAs
- `peopleInData` - counts the number of people in the dataset
- `peopleInState [STATE]` counts the number of people in the state (abbreviation)
- `peopleInPuma [STATE] [PUMA]` counts the number of people in the puma
- `householdsInData` - counts the number of households in the dataset
- `householdsInState [STATE]` - counts the number of households in the state (abbreviation)
- `householdsInPuma [STATE] [PUMA]` - counts the number of households in the puma
- `pumasInState [STATE]` - displays all PUMAs and their human-readable names in [STATE]

### Example Commands

- `pctInsured` - Percentage of people in the currently downloaded dataset who have health insurance

- `multilingualWorkersNoHIByRace` - Percentage of multilingual workers without health insurance coverage, grouped by race, in the currently downloaded dataset

- `bellwether puma` - Calculates the top 10 bellwether pumas in the currently downloaded dataset and shows their Mahalonobis distances and p values. 

- `bellwether state` - Calculates the top 10 “bellwether states” in the U.S. and shows their Mahalonobis distances and p values. (must have entire U.S. downloaded)

- `pull all` - Pulls the entire US dataset 

- `pull NY` - Pulls the New York dataset 

- `datapreview Household` - Shows the first 15 rows in the Household table

- `eligibleVotersByPuma` - Shows the number of eligible voters and percentage of eligible voters in each PUMA

- `rowsIn Person` - Shows the number of rows in the Person table in the downloaded dataset

- `peopleInData` - Shows the number of people in the downloaded dataset
