/* Q23: LEFT JOIN with WHERE filter */
SELECT c.CustomerID, o.OrderTotal
FROM Customers c
LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
WHERE o.OrderTotal > 100;