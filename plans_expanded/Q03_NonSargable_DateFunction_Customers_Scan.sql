/* Q3 — Non-sargable YEAR() filter (scan expected) */
SELECT CustomerID
FROM Customers
WHERE YEAR(CreatedDate) = 2025;