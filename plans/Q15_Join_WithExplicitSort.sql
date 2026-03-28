/* Q15 — Explicit sort after join */
SELECT c.CustomerID, o.OrderTotal
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
ORDER BY o.OrderTotal;