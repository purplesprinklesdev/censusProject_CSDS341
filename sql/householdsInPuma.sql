SELECT SUM(Household_Weight) AS Households
FROM Household
WHERE State = (SELECT State FROM State WHERE abbrev = ?)
AND PUMA = ?;
