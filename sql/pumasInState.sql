SELECT pu.PUMA, pu.name
FROM PUMA pu
JOIN State s
ON pu.State = s.State
WHERE s.abbrev = ?;
