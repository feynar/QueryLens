/* ============================================================
   QueryLens – Static Analysis Test Suite (Week 6)
   ============================================================ */


/* S1 — SELECT * */
-- EXPECT: SELECT_STAR
SELECT *
FROM Customers;


/* S2 — Non-sargable predicate */
-- EXPECT: NON_SARGABLE_PREDICATE
SELECT CustomerID
FROM Customers
WHERE YEAR(CreatedDate) = 2024;


/* S3 — Function in WHERE clause */
-- EXPECT: NON_SARGABLE_PREDICATE
SELECT CustomerID
FROM Customers
WHERE UPPER(FirstName) = 'ALICE';


/* S4 — Implicit type conversion */
-- EXPECT: (future rule) IMPLICIT_CONVERSION
SELECT *
FROM Orders
WHERE OrderID = '1001';


/* S5 — Missing JOIN condition */
-- EXPECT: (future rule) MISSING_JOIN_CONDITION
SELECT *
FROM Customers c, Orders o;


/* S6 — Unfiltered aggregation */
-- EXPECT: (future rule) UNFILTERED_AGGREGATION
SELECT COUNT(*)
FROM Orders;


/* S7 — Correlated subquery */
-- EXPECT: (future rule) CORRELATED_SUBQUERY
SELECT c.CustomerID,
       (SELECT COUNT(*) FROM Orders o WHERE o.CustomerID = c.CustomerID)
FROM Customers c;


/* S8 — ORDER BY non-indexed column */
-- EXPECT: (future rule) ORDER_BY_NO_INDEX
SELECT *
FROM Customers
ORDER BY FirstName;


/* S9 — Redundant subquery */
-- EXPECT: (future rule) REDUNDANT_SUBQUERY
SELECT *
FROM Customers
WHERE CustomerID IN (SELECT CustomerID FROM Customers);


/* S10 — Complex join */
-- EXPECT: COMPLEX_JOIN
SELECT c.CustomerID, o.OrderID
FROM Customers c
JOIN Orders o ON c.CustomerID = o.CustomerID
JOIN Orders o2 ON o.CustomerID = o2.CustomerID;
