/* Q8 — Three-table join with aggregation (Hash Join expected) */
SELECT c.CustomerID, SUM(o.OrderTotal)
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID;