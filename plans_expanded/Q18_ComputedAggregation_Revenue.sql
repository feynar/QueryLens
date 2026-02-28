/* Q18 — Multi-join with computed expression */
SELECT c.CustomerID, SUM(oi.Quantity * oi.UnitPrice)
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
JOIN OrderItems oi ON o.OrderID = oi.OrderID
GROUP BY c.CustomerID;