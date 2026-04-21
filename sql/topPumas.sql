SELECT SUM(p.Person_Weight) AS estimated_population, pu.name
FROM Person p
LEFT JOIN PUMA pu
    ON p.PUMA = pu.PUMA
    AND p.State = pu.State
GROUP BY p.PUMA, p.State
ORDER BY estimated_population DESC
LIMIT 10
