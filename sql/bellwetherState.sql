WITH StatePersonAgg AS (
    SELECT
        p.State,
        SUM(p.Age * p.Person_Weight) / SUM(p.Person_Weight) AS avg_age,
        SUM(p.Weeks_Worked * p.Person_Weight) / SUM(p.Person_Weight) AS avg_weeks_worked,

        SUM(CASE WHEN p.Sex = 1 THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_male,
        SUM(CASE WHEN p.Sex = 2 THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_female,

        SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name='White') THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_race_white,
        SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name='Black') THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_race_black,
        SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name='Asian') THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_race_asian,
        SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name='American Indian') THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_race_american_indian,
        SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name='Alaska Native') THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_race_alaska_native,
        SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name='Native Hawaiian and Other Pacific Islander') THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_race_native_hawaiian_pacific_islander,
        SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name='Some Other Race') THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_some_other_race,
        SUM(CASE WHEN p.Race = (SELECT id FROM Race WHERE name='Two or More Races') THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_two_or_more_races,

        SUM(CASE WHEN p.Ethnicity <> 1 THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_hispanic,
        SUM(CASE WHEN p.Multilingual = 1 THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_english_only,
        SUM(CASE WHEN p.English_Ability IN (1,2) THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_english_well,
        SUM(CASE WHEN p.Decade_of_Immigration IS NOT NULL THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_immigrant,
        SUM(CASE WHEN p.Health_Insurance = 1 THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_health_insured,
        SUM(CASE WHEN p.Citizenship_Status IN (1,2) THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_citizen,

        SUM(CASE WHEN p.Educational_Attainment >= 21 THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_bachelors_or_higher,
        SUM(CASE WHEN p.Marital_Status = 1 THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_married,
        SUM(CASE WHEN p.Employment_Status IN (1,2,4,5) THEN p.Person_Weight ELSE 0 END) / SUM(p.Person_Weight) AS pct_in_labor_force

    FROM Person p
    GROUP BY p.State
),

StateHouseholdAgg AS (
    SELECT
        h.State,
        SUM(h.Household_Income * h.Household_Weight) / SUM(h.Household_Weight) AS avg_household_income,
        SUM(h.Gross_Rent * h.Household_Weight) / SUM(h.Household_Weight) AS avg_gross_rent_pct_income,
        SUM(h.Property_Taxes * h.Household_Weight) / SUM(h.Household_Weight) AS avg_property_taxes,

        SUM(CASE WHEN h.Tenure = 1 THEN h.Household_Weight ELSE 0 END) / SUM(h.Household_Weight) AS pct_owner_occupied,
        SUM(CASE WHEN h.Tenure = 3 THEN h.Household_Weight ELSE 0 END) / SUM(h.Household_Weight) AS pct_renter_occupied,
        SUM(CASE WHEN h.Household_Children IS NOT NULL AND h.Household_Children <> 1 THEN h.Household_Weight ELSE 0 END) / SUM(h.Household_Weight) AS pct_children_present,
        SUM(CASE WHEN h.Workers_in_Family >= 1 THEN h.Household_Weight ELSE 0 END) / SUM(h.Household_Weight) AS pct_worker_in_family

    FROM Household h
    GROUP BY h.State
),

StateProfile AS (
    SELECT
        s.abbrev AS State_Abbreviation,
        pa.*,
        ha.avg_household_income,
        ha.avg_gross_rent_pct_income,
        ha.avg_property_taxes,
        ha.pct_owner_occupied,
        ha.pct_renter_occupied,
        ha.pct_children_present,
        ha.pct_worker_in_family
    FROM StatePersonAgg pa
    JOIN StateHouseholdAgg ha ON pa.State = ha.State
    JOIN State s ON pa.State = s.State
);
