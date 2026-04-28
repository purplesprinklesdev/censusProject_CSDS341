SELECT CAST(SUM(Age * Person_Weight) AS REAL) / SUM(Person_Weight) AS weighted_avg_age
FROM Person
