-- Q3: Hash Join (large unsorted join)
SELECT c.CustomerID, SUM(o.OrderTotal)
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID;

-- Expected: Hash Match + Aggregate