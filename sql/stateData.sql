WITH StatePersonAgg AS (
    SELECT
        p.STATE AS state_abbr,
        SUM(p.AGEP * p.PWGTP) / SUM(p.PWGTP) AS avg_age,
        SUM(e.WKWN * p.PWGTP) / SUM(p.PWGTP) AS avg_weeks_worked,
        SUM(CASE WHEN p.SEX = 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_male,
        SUM(CASE WHEN p.SEX = 2 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_female,

        SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name='White') THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_white,
        SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name='Black') THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_black,
        SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name='Asian') THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_asian,
        SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name='American Indian') THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_american_indian,
        SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name='Alaska Native') THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_alaska_native,
        SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name='Native Hawaiian and Other Pacific Islander') THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_race_native_hawaiian_pacific_islander,
        SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name='Some Other Race') THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_some_other_race,
        SUM(CASE WHEN p.RAC1P = (SELECT id FROM Race WHERE name='Two or More Races') THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_two_or_more_races,

        SUM(CASE WHEN p.HISP <> 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_hispanic,

        SUM(CASE WHEN ed.SCHL >= 21 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_bachelors_or_higher,

        SUM(CASE WHEN e.WIF >= 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_worker_in_family,
        SUM(CASE WHEN p.MAR = 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_married,
        SUM(CASE WHEN e.ESR IN (1,2,4,5) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_in_labor_force,

        SUM(CASE WHEN p.LANX = 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_english_only,
        SUM(CASE WHEN p.ENG IN (1,2) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_english_well,
        SUM(CASE WHEN p.DECADE IS NOT NULL THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_immigrant,
        SUM(CASE WHEN p.HICOV = 1 THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_health_insured,
        SUM(CASE WHEN p.CIT IN (1,2) THEN p.PWGTP ELSE 0 END) / SUM(p.PWGTP) AS pct_citizen

    FROM Person p
    LEFT JOIN Employment e
        ON p.SERIALNO = e.SERIALNO
       AND p.SPORDER = e.SPORDER
    LEFT JOIN Education ed
        ON p.SERIALNO = ed.SERIALNO
       AND p.SPORDER = ed.SPORDER
    GROUP BY p.STATE
),
StateHouseholdAgg AS (
    SELECT
        h.STATE AS state_abbr,

        SUM(h.HINCP * h.WGTP) / SUM(h.WGTP) AS avg_household_income,
        SUM(hu.GRPIP * h.WGTP) / SUM(h.WGTP) AS avg_gross_rent_pct_income,
        SUM(hu.TAXAMT * h.WGTP) / SUM(h.WGTP) AS avg_property_taxes,

        SUM(CASE WHEN hu.TEN = 1 THEN h.WGTP ELSE 0 END) / SUM(h.WGTP) AS pct_owner_occupied,
        SUM(CASE WHEN hu.TEN = 3 THEN h.WGTP ELSE 0 END) / SUM(h.WGTP) AS pct_renter_occupied,
        SUM(CASE WHEN h.HUPAC IS NOT NULL AND h.HUPAC <> 1 THEN h.WGTP ELSE 0 END) / SUM(h.WGTP) AS pct_children_present

    FROM Household h
    LEFT JOIN HousingUnit hu
        ON h.SERIALNO = hu.SERIALNO
    GROUP BY h.STATE
),

StateProfile AS (
    SELECT
        s.State_Name,
        pa.*,
        ha.avg_household_income,
        ha.avg_gross_rent_pct_income,
        ha.avg_property_taxes,
        ha.pct_owner_occupied,
        ha.pct_renter_occupied,
        ha.pct_children_present
    FROM StatePersonAgg pa
    LEFT JOIN StateHouseholdAgg ha ON pa.state_abbr = ha.state_abbr
    LEFT JOIN State s ON pa.state_abbr = s.State_Abbreviation
),

National AS (
    SELECT
        AVG(avg_age) AS nat_avg_age,
        AVG(avg_weeks_worked) AS nat_avg_weeks_worked,
        AVG(pct_male) AS nat_pct_male,
        AVG(pct_female) AS nat_pct_female,
        AVG(pct_race_white) AS nat_pct_race_white,
        AVG(pct_race_black) AS nat_pct_race_black,
        AVG(pct_race_asian) AS nat_pct_race_asian,
        AVG(pct_race_american_indian) AS nat_pct_race_american_indian,
        AVG(pct_race_alaska_native) AS nat_pct_race_alaska_native,
        AVG(pct_race_native_hawaiian_pacific_islander) AS nat_pct_race_native_hawaiian_pacific_islander,
        AVG(pct_some_other_race) AS nat_pct_some_other_race,
        AVG(pct_two_or_more_races) AS nat_pct_two_or_more_races,
        AVG(pct_hispanic) AS nat_pct_hispanic,
        AVG(pct_bachelors_or_higher) AS nat_pct_bachelors_or_higher,
        AVG(pct_worker_in_family) AS nat_pct_worker_in_family,
        AVG(pct_married) AS nat_pct_married,
        AVG(pct_in_labor_force) AS nat_pct_in_labor_force,
        AVG(pct_english_only) AS nat_pct_english_only,
        AVG(pct_english_well) AS nat_pct_english_well,
        AVG(pct_immigrant) AS nat_pct_immigrant,
        AVG(pct_health_insured) AS nat_pct_health_insured,
        AVG(pct_citizen) AS nat_pct_citizen,
        AVG(avg_household_income) AS nat_avg_household_income,
        AVG(avg_gross_rent_pct_income) AS nat_avg_gross_rent_pct_income,
        AVG(avg_property_taxes) AS nat_avg_property_taxes,
        AVG(pct_owner_occupied) AS nat_pct_owner_occupied,
        AVG(pct_renter_occupied) AS nat_pct_renter_occupied,
        AVG(pct_children_present) AS nat_pct_children_present
    FROM StateProfile
)

SELECT
    sp.State_Name,
    sp.state_abbr,
    (
        ABS(sp.avg_age - n.nat_avg_age) / NULLIF(n.nat_avg_age, 0) +
        ABS(sp.pct_male - n.nat_pct_male) / NULLIF(n.nat_pct_male, 0) +
        ABS(sp.pct_hispanic - n.nat_pct_hispanic) / NULLIF(n.nat_pct_hispanic, 0) +
        ABS(sp.pct_race_white - n.nat_pct_race_white) / NULLIF(n.nat_pct_race_white, 0) +
        ABS(sp.pct_race_black - n.nat_pct_race_black) / NULLIF(n.nat_pct_race_black, 0) +
        ABS(sp.pct_race_asian - n.nat_pct_race_asian) / NULLIF(n.nat_pct_race_asian, 0) +
        ABS(sp.pct_race_american_indian - n.nat_pct_race_american_indian) / NULLIF(n.nat_pct_race_american_indian, 0) +
        ABS(sp.pct_race_alaska_native - n.nat_pct_race_alaska_native) / NULLIF(n.nat_pct_race_alaska_native, 0) +
        ABS(sp.pct_race_native_hawaiian_pacific_islander - n.nat_pct_race_native_hawaiian_pacific_islander) / NULLIF(n.nat_pct_race_native_hawaiian_pacific_islander, 0) +
        ABS(sp.pct_some_other_race - n.nat_pct_some_other_race) / NULLIF(n.nat_pct_some_other_race, 0) +
        ABS(sp.pct_two_or_more_races - n.nat_pct_two_or_more_races) / NULLIF(n.nat_pct_two_or_more_races, 0) +
        ABS(sp.pct_bachelors_or_higher - n.nat_pct_bachelors_or_higher) / NULLIF(n.nat_pct_bachelors_or_higher, 0) +
        ABS(sp.pct_worker_in_family - n.nat_pct_worker_in_family) / NULLIF(n.nat_pct_worker_in_family, 0) +
        ABS(sp.avg_weeks_worked - n.nat_avg_weeks_worked) / NULLIF(n.nat_avg_weeks_worked, 0) +
        ABS(sp.pct_owner_occupied - n.nat_pct_owner_occupied) / NULLIF(n.nat_pct_owner_occupied, 0) +
        ABS(sp.avg_household_income - n.nat_avg_household_income) / NULLIF(n.nat_avg_household_income, 0) +
        ABS(sp.pct_children_present - n.nat_pct_children_present) / NULLIF(n.nat_pct_children_present, 0) +
        ABS(sp.avg_gross_rent_pct_income - n.nat_avg_gross_rent_pct_income) / NULLIF(n.nat_avg_gross_rent_pct_income, 0) +
        ABS(sp.avg_property_taxes - n.nat_avg_property_taxes) / NULLIF(n.nat_avg_property_taxes, 0) +
        ABS(sp.pct_married - n.nat_pct_married) / NULLIF(n.nat_pct_married, 0) +
        ABS(sp.pct_in_labor_force - n.nat_pct_in_labor_force) / NULLIF(n.nat_pct_in_labor_force, 0) +
        ABS(sp.pct_english_only - n.nat_pct_english_only) / NULLIF(n.nat_pct_english_only, 0) +
        ABS(sp.pct_english_well - n.nat_pct_english_well) / NULLIF(n.nat_pct_english_well, 0) +
        ABS(sp.pct_immigrant - n.nat_pct_immigrant) / NULLIF(n.nat_pct_immigrant, 0) +
        ABS(sp.pct_health_insured - n.nat_pct_health_insured) / NULLIF(n.nat_pct_health_insured, 0) +
        ABS(sp.pct_citizen - n.nat_pct_citizen) / NULLIF(n.nat_pct_citizen, 0)
    ) AS bellwether_score
FROM StateProfile sp
CROSS JOIN National n
ORDER BY bellwether_score ASC;
