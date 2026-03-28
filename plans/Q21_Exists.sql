/* Q21: EXISTS Subquery */
SELECT c.CustomerID
FROM Customers c
WHERE EXISTS (
    SELECT 1 FROM Orders o
    WHERE o.CustomerID = c.CustomerID
);