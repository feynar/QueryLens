/* Q4 — Function in predicate (scan expected) */
SELECT CustomerID
FROM Customers
WHERE UPPER(FirstName) = 'FIRST100';