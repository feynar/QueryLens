-- Q2: Index Scan (non-sargable)
SELECT *
FROM Customers
WHERE YEAR(CreatedDate) = 2025;

-- Expected: Index Scan + Compute Scalar