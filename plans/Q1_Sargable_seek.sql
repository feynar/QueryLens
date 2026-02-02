-- Q1: Index Seek (sargable)
SELECT *
FROM Customers
WHERE CreatedDate >= '2024-01-01';

-- Expected: Index Seek on IX_Customers_CreatedDate