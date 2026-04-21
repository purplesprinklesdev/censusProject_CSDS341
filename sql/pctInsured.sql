SELECT
    SUM(CASE WHEN Health_Insurance = 1 THEN Person_Weight ELSE 0 END) * 100.0
        / SUM(Person_Weight) AS pct_insured
FROM Person
