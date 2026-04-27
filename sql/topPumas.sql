SELECT 
    pu.name AS PUMA_Name,
    SUM(p.Person_Weight) AS estimated_population
FROM Person p
LEFT JOIN PUMA pu
    ON p.PUMA = pu.PUMA
    AND p.State = pu.State
GROUP BY p.PUMA, p.State, pu.name
ORDER BY estimated_population DESC
LIMIT 10
