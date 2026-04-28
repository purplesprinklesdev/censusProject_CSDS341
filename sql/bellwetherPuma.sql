CREATE VIEW PumaProfile AS
WITH PersonAgg AS (
    SELECT
        p.State,
        p.PUMA,


        CAST(SUM(p.Age * p.Person_Weight) AS REAL)          / NULLIF(SUM(p.Person_Weight), 0) AS avg_age,
        CAST(SUM(p.Weeks_Worked * p.Person_Weight) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS avg_weeks_worked,

        CAST(SUM(CASE WHEN p.Sex = 1 THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_male,
        CAST(SUM(CASE WHEN p.Sex = 2 THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_female,

        CAST(SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name = 'White')                              THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_race_white,
        CAST(SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name = 'Black')                              THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_race_black,
        CAST(SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name = 'Asian')                              THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_race_asian,
        CAST(SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name = 'American Indian')                    THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_race_american_indian,
        CAST(SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name = 'Alaska Native')                      THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_race_alaska_native,
        CAST(SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name = 'Native Hawaiian or Pacific Islander') THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_race_native_hawaiian_pacific_islander,
        CAST(SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name = 'Some Other Race')                    THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_some_other_race,
        CAST(SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name = 'Two or More Races')                  THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_two_or_more_races,

        CAST(SUM(CASE WHEN p.Ethnicity <> 1 THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_hispanic,

        CAST(SUM(CASE WHEN p.Educational_Attainment >= 22                                          THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_masters_or_higher,
        CAST(SUM(CASE WHEN p.Educational_Attainment = 21                                           THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_bachelors,
        CAST(SUM(CASE WHEN p.Educational_Attainment > 17 AND p.Educational_Attainment <= 20        THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_some_college,
        CAST(SUM(CASE WHEN p.Educational_Attainment = 16 OR p.Educational_Attainment = 17         THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_high_school_diploma,
        CAST(SUM(CASE WHEN p.Educational_Attainment < 16                                           THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_less_than_high_school,

        CAST(SUM(CASE WHEN p.Marital_Status = 1                THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_married,
        CAST(SUM(CASE WHEN p.Employment_Status IN (1,2,4,5)    THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_in_labor_force,
        CAST(SUM(CASE WHEN p.Multilingual = 1                  THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_english_only,
        CAST(SUM(CASE WHEN p.English_Ability IN (1,2)          THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_english_well,
        CAST(SUM(CASE WHEN p.Decade_of_Immigration <> 0        THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_immigrant,
        CAST(SUM(CASE WHEN p.Health_Insurance = 1              THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_health_insured,
        CAST(SUM(CASE WHEN p.Citizenship_Status IN (1,2)       THEN p.Person_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(p.Person_Weight), 0) AS pct_citizen

    FROM Person p
    GROUP BY p.State, p.PUMA
),

HouseholdAgg AS (
    SELECT
        h.State,
        h.PUMA,

        CAST(SUM(h.Household_Income  * h.Household_Weight) AS REAL) / NULLIF(SUM(h.Household_Weight), 0) AS avg_household_income,
        CAST(SUM(h.Gross_Rent        * h.Household_Weight) AS REAL) / NULLIF(SUM(h.Household_Weight), 0) AS avg_gross_rent,
        CAST(SUM(h.Property_Taxes    * h.Household_Weight) AS REAL) / NULLIF(SUM(h.Household_Weight), 0) AS avg_property_taxes,
        CAST(SUM(h.Property_Value    * h.Household_Weight) AS REAL) / NULLIF(SUM(h.Household_Weight), 0) AS avg_property_value,

        CAST(SUM(CASE WHEN h.Tenure IN (1, 2)       THEN h.Household_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(h.Household_Weight), 0) AS pct_owner_occupied,
        CAST(SUM(CASE WHEN h.Tenure = 3              THEN h.Household_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(h.Household_Weight), 0) AS pct_renter_occupied,
        CAST(SUM(CASE WHEN h.Household_Children = 1  THEN h.Household_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(h.Household_Weight), 0) AS pct_children_present,
        CAST(SUM(CASE WHEN h.Workers_in_Family = 1  THEN h.Household_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(CASE WHEN h.Workers_in_Family = -1 THEN 0 ELSE h.Household_Weight END), 0) AS pct_one_worker,
        CAST(SUM(CASE WHEN h.Workers_in_Family = 2  THEN h.Household_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(CASE WHEN h.Workers_in_Family = -1 THEN 0 ELSE h.Household_Weight END), 0) AS pct_two_workers,
        CAST(SUM(CASE WHEN h.Workers_in_Family = 3  THEN h.Household_Weight ELSE 0 END) AS REAL) / NULLIF(SUM(CASE WHEN h.Workers_in_Family = -1 THEN 0 ELSE h.Household_Weight END), 0) AS pct_three_or_more_workers

    FROM Household h
    GROUP BY h.State, h.PUMA
)

SELECT
    s.abbrev AS STATE,
    pa.PUMA,
    pu.name AS Puma_Name,

    pa.avg_age,
    pa.avg_weeks_worked,
    pa.pct_male,
    pa.pct_female,
    pa.pct_race_white,
    pa.pct_race_black,
    pa.pct_race_asian,
    pa.pct_race_american_indian,
    pa.pct_race_alaska_native,
    pa.pct_race_native_hawaiian_pacific_islander,
    pa.pct_some_other_race,
    pa.pct_two_or_more_races,
    pa.pct_hispanic,
    pa.pct_masters_or_higher,
    pa.pct_bachelors,
    pa.pct_some_college,
    pa.pct_high_school_diploma,
    pa.pct_less_than_high_school,
    pa.pct_married,
    pa.pct_in_labor_force,
    pa.pct_english_only,
    pa.pct_english_well,
    pa.pct_immigrant,
    pa.pct_health_insured,
    pa.pct_citizen,

    ha.avg_household_income,
    ha.avg_gross_rent,
    ha.avg_property_taxes,
    ha.avg_property_value,
    ha.pct_owner_occupied,
    ha.pct_renter_occupied,
    ha.pct_children_present,
    ha.pct_one_worker,
    ha.pct_two_workers,
    ha.pct_three_or_more_workers

FROM PersonAgg pa
JOIN HouseholdAgg ha
    ON  pa.State = ha.State
    AND pa.PUMA  = ha.PUMA
JOIN PUMA pu
    ON  pa.PUMA  = pu.PUMA
    AND pa.State = pu.State
JOIN State s
    ON pa.State = s.State;
