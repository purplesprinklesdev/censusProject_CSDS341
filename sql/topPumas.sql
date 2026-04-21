SELECT PUMA, SUM(Person_Weight) AS estimated_population
FROM Person
GROUP BY PUMA
ORDER BY estimated_population DESC
LIMIT 10
