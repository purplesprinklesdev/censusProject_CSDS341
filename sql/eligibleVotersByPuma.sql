SELECT
    s.abbrev                                                                AS State_Abbrev,
    p.PUMA,
    SUM(p.Person_Weight)                                                    AS Total_Weighted_Population,
    SUM(CASE WHEN p.Citizenship_Status IN (1, 2, 3)
             AND p.Age >= 18
             THEN p.Person_Weight ELSE 0 END)                               AS Weighted_Eligible_Voters,
    ROUND(100.0 * CAST(SUM(CASE WHEN p.Citizenship_Status IN (1, 2, 3)
                               AND p.Age >= 18
                               THEN p.Person_Weight ELSE 0 END) AS REAL) /
          NULLIF(SUM(p.Person_Weight), 0), 2)                               AS Pct_Eligible_Voters
FROM Person p
JOIN State s ON p.State = s.State
GROUP BY s.abbrev, p.PUMA
ORDER BY Pct_Eligible_Voters DESC;
