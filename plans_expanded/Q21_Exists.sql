/* Q21: EXISTS Subquery */
SELECT TOP 1000 *
FROM Customers c
WHERE EXISTS (
    SELECT 1 FROM Orders o
    WHERE o.CustomerID = c.CustomerID
);