SELECT
    SUM(CASE WHEN Employment_Status IN (1, 2, 4, 5) THEN Person_Weight ELSE 0 END) * 100.0
        / SUM(Person_Weight) AS pct_in_labor_force
FROM Person
WHERE Age BETWEEN 16 AND 64
