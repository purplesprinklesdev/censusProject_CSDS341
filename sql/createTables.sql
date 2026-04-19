CREATE TABLE Person (
    Serial_No TEXT,
    Person_ID INTEGER,
    PUMA INTEGER,
    Person_Weight INTEGER,
    Sex INTEGER,
    Race INTEGER,
    Ethnicity INTEGER,
    Age INTEGER,
    Marital_Status INTEGER,
    Health_Insurance INTEGER,
    Employment_Status INTEGER,
    Weeks_Worked INTEGER,
    Multilingual INTEGER,
    English_Ability INTEGER,
    Decade_of_Immigration INTEGER,
    Citizenship_Status INTEGER,
    Educational_Attainment INTEGER,
    State INTEGER,
    PRIMARY KEY (Serial_No, Person_ID)
);
CREATE TABLE Household (
    Serial_No TEXT,
    PUMA INTEGER,
    Household_Weight INTEGER,
    Household_Income INTEGER,
    Property_Value INTEGER,
    Household_Children INTEGER,
    Gross_Rent INTEGER,
    Property_Taxes INTEGER,
    Tenure INTEGER,
    Workers_in_Family INTEGER,
    State INTEGER,
    PRIMARY KEY (Serial_No)
);
CREATE TABLE State (
    State INTEGER,
    abbrev TEXT,
    PRIMARY KEY (State)
);
CREATE TABLE PUMA (
    PUMA INTEGER,
    State INTEGER,
    PRIMARY KEY (PUMA)
);
CREATE TABLE Race (
    id INTEGER,
    name TEXT,
    PRIMARY KEY (id)
);
