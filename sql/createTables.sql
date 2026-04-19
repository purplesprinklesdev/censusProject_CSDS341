CREATE TABLE Person (
    Serial_No INTEGER,
    Person_ID INTEGER,
    PUMA INTEGER,
    Person_Weight INTEGER,
    Sex INTEGER,
    Race INTEGER,
    Ethnicity INTEGER,
    Age INTEGER,
    Educational_Attainment INTEGER,
    Marital_Status INTEGER,
    Employment_Status INTEGER,
    State INTEGER,
    PRIMARY KEY (Serial_No, Person_ID)
);
CREATE TABLE Household (
    Serial_No INTEGER,
    PUMA INTEGER,
    Household_Weight INTEGER,
    Household_Income INTEGER,
    Property_Value INTEGER,
    Household_Children INTEGER,
    Gross_Rent INTEGER,
    Property_Taxes INTEGER,
    State INTEGER,
    PRIMARY KEY (Serial_No)
);
CREATE TABLE State (
    State INTEGER,
    State_Abbrev TEXT,
    PRIMARY KEY (State)
);
