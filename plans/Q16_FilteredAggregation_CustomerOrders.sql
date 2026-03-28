/* Q16 — Join with aggregation and filter */
SELECT c.CustomerID, COUNT(o.OrderID)
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
WHERE o.OrderDate >= '2024-01-01'
GROUP BY c.CustomerID;