-- Q4: Merge Join (sorted inputs)
SELECT c.CustomerID, o.OrderTotal
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
ORDER BY c.CustomerID;

-- Expected: Merge Join + Sort (unless optimizer eliminates sort)