SELECT SUM(Person_Weight) AS People
FROM Person
WHERE State = (SELECT State FROM State WHERE abbrev = ?);
