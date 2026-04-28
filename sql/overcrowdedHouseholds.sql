SELECT
    s.abbrev                                      AS State,
    pu.name                                       AS PUMA,
    SUM(h.Household_Weight)                       AS Weighted_Qualifying_Households,
    ROUND(CAST(SUM(h.Household_Income * h.Household_Weight) AS REAL) /
          NULLIF(SUM(h.Household_Weight), 0), 2)  AS Weighted_Avg_Income,
    ROUND(CAST(SUM(h.Household_Children * h.Household_Weight) AS REAL) /
          NULLIF(SUM(h.Household_Weight), 0), 2)  AS Weighted_Avg_Children
FROM Household h
JOIN State s
ON h.State = s.State
JOIN PUMA pu
ON h.PUMA = pu.PUMA
WHERE
    h.Household_Children  >= 3
    AND h.Workers_in_Family   <= 1
    AND h.Household_Income BETWEEN 1 AND 40000
    AND h.Tenure IN (2, 3)
GROUP BY h.PUMA
ORDER BY Weighted_Qualifying_Households DESC
LIMIT 50;
