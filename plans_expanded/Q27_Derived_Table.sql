/* Q27: Derived table */
SELECT *
FROM (
    SELECT CustomerID, SUM(OrderTotal) AS TotalSpent
    FROM Orders
    GROUP BY CustomerID
) t
WHERE t.TotalSpent > 500;