USE QueryLensDB;
GO

-- Q1: Index Seek (sargable)
SELECT *
FROM Customers
WHERE CreatedDate >= '2024-01-01';

-- Expected: Index Seek on IX_Customers_CreatedDate


-- Q2: Index Scan (non-sargable)
SELECT *
FROM Customers
WHERE YEAR(CreatedDate) = 2024;

-- Expected: Index Scan + Compute Scalar


-- Q3: Hash Join (large unsorted join)
SELECT c.CustomerID, SUM(o.OrderTotal)
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID;

-- Expected: Hash Match + Aggregate


-- Q4: Merge Join (sorted inputs)
SELECT c.CustomerID, o.OrderTotal
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
ORDER BY c.CustomerID;

-- Expected: Merge Join + Sort (unless optimizer eliminates sort)


-- Q5: Sort operator
SELECT *
FROM Orders
ORDER BY OrderTotal;

-- Expected: Sort
