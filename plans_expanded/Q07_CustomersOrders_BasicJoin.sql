/* Q7 — Simple join Customers → Orders (Nested Loop or Merge) */
SELECT c.CustomerID, o.OrderID
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID;