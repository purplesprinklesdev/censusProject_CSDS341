SELECT SUM(Person_Weight)
FROM Person
WHERE Age < 20;

-- the reason this works is that "person_weight" corresponds to the number of
-- actual people in Ohio "represented" by a given row in the Census.