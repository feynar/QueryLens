/* Q29: Multi-condition predicate */
SELECT *
FROM Customers
WHERE CreatedDate >= '2023-01-01'
AND FirstName LIKE 'First4%';