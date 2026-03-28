/* Q24: CROSS JOIN */
SELECT TOP 1000 c.CustomerID, o.OrderID
FROM Customers c
CROSS JOIN Orders o;