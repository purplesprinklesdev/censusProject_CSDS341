SELECT
    PUMA
    SUM(h.Household_Weight)                       AS Weighted_Qualifying_Households,
    ROUND(CAST(SUM(h.Household_Income * h.Household_Weight) AS REAL) /
          NULLIF(SUM(h.Household_Weight), 0), 2)  AS Weighted_Avg_Income,
    ROUND(CAST(SUM(h.Household_Children * h.Household_Weight) AS REAL) /
          NULLIF(SUM(h.Household_Weight), 0), 2)  AS Weighted_Avg_Children
FROM Household h
WHERE
    Household_Children  >= 3
    AND Workers_in_Family   <= 1
    AND Household_Income BETWEEN 1 AND 40000
    AND Tenure IN (2, 3)
GROUP BY PUMA
ORDER BY Weighted_Qualifying_Households DESC;
