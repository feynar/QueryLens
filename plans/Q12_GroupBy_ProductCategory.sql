/* Q12 — GROUP BY with join fan-out */
SELECT p.Category, COUNT(*)
FROM Products p
JOIN OrderItems oi ON p.ProductID = oi.ProductID
GROUP BY p.Category;