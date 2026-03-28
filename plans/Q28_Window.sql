/* Q28: Window function */
SELECT CustomerID,
       ROW_NUMBER() OVER (PARTITION BY CustomerID ORDER BY OrderDate) AS rn
FROM Orders;