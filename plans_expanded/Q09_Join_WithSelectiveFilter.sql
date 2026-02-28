/* Q9 — Join with selective filter */
SELECT o.OrderID, o.OrderTotal
FROM Orders o
JOIN Customers c ON o.CustomerID = c.CustomerID
WHERE c.CreatedDate >= '2024-01-01';