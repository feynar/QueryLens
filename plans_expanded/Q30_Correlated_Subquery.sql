/* Q30: Correlated subquery */
SELECT c.CustomerID,
       (SELECT COUNT(*) FROM Orders o WHERE o.CustomerID = c.CustomerID)
FROM Customers c;