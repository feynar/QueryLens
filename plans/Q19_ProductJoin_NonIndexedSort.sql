/* Q19 — Join with non-indexed ORDER BY */
SELECT p.ProductName, oi.Quantity
FROM Products p
JOIN OrderItems oi ON p.ProductID = oi.ProductID
ORDER BY p.ProductName;