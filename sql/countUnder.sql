SELECT SUM(Person_Weight) AS People
FROM Person
WHERE Age < ?;

-- the reason this works is that "person_weight" corresponds to the number of
-- actual people in Ohio "represented" by a given row in the Census.
