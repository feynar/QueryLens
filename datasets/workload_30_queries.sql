/* ============================================================
   QueryLens — Expanded Runtime Validation Workload (Week 14)
   Schema: Customers, Orders, Products, OrderItems
   ============================================================ */

USE QueryLensDB;

/* Q1 — SELECT * full table scan */
SELECT *
FROM Customers;


/* Q2 — Sargable indexed filter (seek expected) */
SELECT CustomerID
FROM Customers
WHERE CreatedDate >= '2024-01-01';


/* Q3 — Non-sargable YEAR() filter (scan expected) */
SELECT CustomerID
FROM Customers
WHERE YEAR(CreatedDate) = 2025;


/* Q4 — Function in predicate (scan expected) */
SELECT CustomerID
FROM Customers
WHERE UPPER(FirstName) = 'FIRST100';


/* Q5 — ORDER BY indexed column (no explicit sort expected) */
SELECT *
FROM Orders
ORDER BY OrderDate;


/* Q6 — ORDER BY non-indexed column (Sort operator expected) */
SELECT *
FROM Customers
ORDER BY FirstName;


/* Q7 — Simple join Customers → Orders (Nested Loop or Merge) */
SELECT c.CustomerID, o.OrderID
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID;


/* Q8 — Three-table join with aggregation (Hash Join expected) */
SELECT c.CustomerID, SUM(o.OrderTotal)
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID;


/* Q9 — Join with selective filter */
SELECT o.OrderID, o.OrderTotal
FROM Orders o
JOIN Customers c ON o.CustomerID = c.CustomerID
WHERE c.CreatedDate >= '2024-01-01';


/* Q10 — Join across full normalized schema */
SELECT c.CustomerID, p.ProductName, oi.Quantity
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
JOIN OrderItems oi ON o.OrderID = oi.OrderID
JOIN Products p ON oi.ProductID = p.ProductID;


/* Q11 — Aggregation over large table */
SELECT SUM(OrderTotal)
FROM Orders;


/* Q12 — GROUP BY with join fan-out */
SELECT p.Category, COUNT(*)
FROM Products p
JOIN OrderItems oi ON p.ProductID = oi.ProductID
GROUP BY p.Category;


/* Q13 — High-selectivity predicate */
SELECT *
FROM Orders
WHERE OrderID = 1000;


/* Q14 — Low-selectivity predicate */
SELECT *
FROM Orders
WHERE OrderDate >= '2024-01-01';


/* Q15 — Explicit sort after join */
SELECT c.CustomerID, o.OrderTotal
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
ORDER BY o.OrderTotal;


/* Q16 — Join with aggregation and filter */
SELECT c.CustomerID, COUNT(o.OrderID)
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
WHERE o.OrderDate >= '2024-01-01'
GROUP BY c.CustomerID;


/* Q17 — Product price filter + join */
SELECT p.ProductName, oi.Quantity
FROM Products p
JOIN OrderItems oi ON p.ProductID = oi.ProductID
WHERE p.Price > 100;


/* Q18 — Multi-join with computed expression */
SELECT c.CustomerID, SUM(oi.Quantity * oi.UnitPrice)
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
JOIN OrderItems oi ON o.OrderID = oi.OrderID
GROUP BY c.CustomerID;


/* Q19 — Join with non-indexed ORDER BY */
SELECT p.ProductName, oi.Quantity
FROM Products p
JOIN OrderItems oi ON p.ProductID = oi.ProductID
ORDER BY p.ProductName;


/* Q20 — Wide retrieval across full schema */
SELECT *
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
JOIN OrderItems oi ON o.OrderID = oi.OrderID
JOIN Products p ON oi.ProductID = p.ProductID;


/* Q21: EXISTS Subquery */
SELECT c.CustomerID
FROM Customers c
WHERE EXISTS (
    SELECT 1 FROM Orders o
    WHERE o.CustomerID = c.CustomerID
);


/* Q22: NOT EXISTS */
SELECT *
FROM Customers c
WHERE NOT EXISTS (
    SELECT 1 FROM Orders o
    WHERE o.CustomerID = c.CustomerID
);


/* Q23: LEFT JOIN with WHERE filter */
SELECT c.CustomerID, o.OrderTotal
FROM Customers c
LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
WHERE o.OrderTotal > 100;


/* Q24: CROSS JOIN */
SELECT TOP 1000 c.CustomerID, o.OrderID
FROM Customers c
CROSS JOIN Orders o;


/* Q25: Aggregation with HAVING */
SELECT CustomerID, COUNT(*) AS OrderCount
FROM Orders
GROUP BY CustomerID
HAVING COUNT(*) > 5;


/* Q26: TOP with ORDER BY */
SELECT TOP 10 *
FROM Orders
ORDER BY OrderTotal DESC;


/* Q27: Derived table */
SELECT *
FROM (
    SELECT CustomerID, SUM(OrderTotal) AS TotalSpent
    FROM Orders
    GROUP BY CustomerID
) t
WHERE t.TotalSpent > 500;


/* Q28: Window function */
SELECT CustomerID,
       ROW_NUMBER() OVER (PARTITION BY CustomerID ORDER BY OrderDate) AS rn
FROM Orders;


/* Q29: Multi-condition predicate */
SELECT *
FROM Customers
WHERE CreatedDate >= '2023-01-01'
AND FirstName LIKE 'First4%';


/* Q30: Correlated subquery */
SELECT c.CustomerID,
       (SELECT COUNT(*) FROM Orders o WHERE o.CustomerID = c.CustomerID)
FROM Customers c;