SELECT
    r.name                                                        AS Race,
    SUM(p.Person_Weight)                                          AS Weighted_Uninsured_Multilingual_Workers,
    ROUND(100.0 * CAST(SUM(p.Person_Weight) AS REAL) /
          NULLIF(SUM(SUM(p.Person_Weight)) OVER (), 0), 2)        AS Pct_of_Total
FROM Person p
JOIN Race r ON p.Race = r.id
WHERE
    p.Multilingual        = 1
    AND p.Health_Insurance    = 2
    AND p.Employment_Status   = 1
    AND p.Age BETWEEN 18 AND 64
GROUP BY r.name
ORDER BY Weighted_Uninsured_Multilingual_Workers DESC;
