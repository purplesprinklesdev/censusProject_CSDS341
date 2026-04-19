WITH PersonAgg AS (
        SELECT
            p.STATE AS state_abbr,
            p.PUMA,

            SUM(p.AGEP * p.PWGTP) / SUM(p.PWGTP) AS avg_age,
            SUM(e.WKWN * p.PWGTP) / SUM(p.PWGTP) AS avg_weeks_worked,

            SUM(CASE WHEN p.SEX = 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_male,
            SUM(CASE WHEN p.SEX = 2 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_female,

            SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name=’White’) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_white,
            SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name=’Black’) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_black,
            SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name=’Asian’) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_asian,
	 SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name=’American Indian’) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_american_indian,
	 SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name=’Alaska Native’) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_alaska_native,
	 SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name=’Native Hawaiian and Other Pacific Islander’) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_native_hawaiian_pacific_islander,
	SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name=’Some Other Race’) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_some_other_race,
	SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name=’Two or More Races’) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_two_or_more_races,

            SUM(CASE WHEN p.HISP <> 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_hispanic,

	SUM(CASE WHEN p.SCHL >= 22 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_masters_or_higher,
            SUM(CASE WHEN p.SCHL = 21 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_bachelors,
SUM(CASE WHEN p.SCHL > 17 AND p.SCHL <= 20 p.SCHL THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_some_college,

SUM(CASE WHEN p.SCHL = 16 OR p.SCHL = 17 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_high_school_diploma,
SUM(CASE WHEN p.SCHL < 16 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_less_than_high_school,


            SUM(CASE WHEN p.MAR = 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_married,
            SUM(CASE WHEN p.ESR IN (1,2,4,5) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_in_labor_force,

            SUM(CASE WHEN p.LANX = 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_english_only,
            SUM(CASE WHEN p.ENG IN (1,2) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_english_well,
            SUM(CASE WHEN p.DECADE IS NOT NULL THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_immigrant,
            SUM(CASE WHEN p.HICOV = 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_health_insured,
            SUM(CASE WHEN p.CIT IN (1,2) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_citizen

        FROM Person p
        GROUP BY p.STATE, p.PUMA
    ),

    HouseholdAgg AS (
        SELECT
            h.STATE AS state_abbr,
            h.PUMA,

            SUM(h.HINCP * h.WGTP) / SUM(h.WGTP) AS avg_household_income,
            SUM(hu.GRPIP * h.WGTP) / SUM(h.WGTP) AS avg_gross_rent_pct_income,
            SUM(hu.TAXAMT * h.WGTP) / SUM(h.WGTP) AS avg_property_taxes,

            SUM(CASE WHEN h.TEN = 1 THEN h.WGTP ELSE 0 END) / SUM(h.WGTP) AS pct_owner_occupied,
            SUM(CASE WHEN h.TEN = 3 THEN h.WGTP ELSE 0 END) / SUM(h.WGTP) AS pct_renter_occupied,
            SUM(CASE WHEN h.HUPAC IS NOT NULL AND h.HUPAC <> 1 THEN h.WGTP ELSE 0 END) / SUM(h.WGTP) AS pct_children_present
	SUM(CASE WHEN h.WIF >= 1 THEN h.WGTP ELSE 0 END) / SUM(h.WGTP) AS pct_worker_in_family,

        FROM Household h
        GROUP BY h.STATE, h.PUMA
    )

CREATE VIEW PumaProfile AS (
SELECT (
        s.State_Name,
        pu.Puma_Name,
        pa.state_abbr,
        pa.PUMA,

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
        pa.pct_bachelors_or_higher,
        pa.pct_worker_in_family,
        pa.pct_married,
        pa.pct_in_labor_force,
        pa.pct_english_only,
        pa.pct_english_well,
        pa.pct_immigrant,
        pa.pct_health_insured,
        pa.pct_citizen,

        ha.avg_household_income,
        ha.avg_gross_rent_pct_income,
        ha.avg_property_taxes,
        ha.pct_owner_occupied,
        ha.pct_renter_occupied,
        ha.pct_children_present

    FROM PersonAgg pa
    LEFT JOIN HouseholdAgg ha
        ON pa.state_abbr = ha.state_abbr
       AND pa.PUMA = ha.PUMA
    LEFT JOIN State s
        ON pa.state_abbr = s.State_Abbreviation
    LEFT JOIN PUMA pu
        ON pa.PUMA = pu.Puma_ID
));
