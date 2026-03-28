/* Q17 — Product price filter + join */
SELECT p.ProductName, oi.Quantity
FROM Products p
JOIN OrderItems oi ON p.ProductID = oi.ProductID
WHERE p.Price > 100;