USE QueryLensDB;
GO

SET NOCOUNT ON;

/* -----------------------------
   Products: 1,000 rows
----------------------------- */
DECLARE @i INT = 1;
WHILE @i <= 1000
BEGIN
    INSERT INTO Products (ProductName, Price, Category)
    VALUES (
        CONCAT('Product', @i),
        (ABS(CHECKSUM(NEWID())) % 50000) / 100.0,
        CONCAT('Category', @i % 20)
    );
    SET @i += 1;
END;

/* -----------------------------
   OrderItems: 400,000 rows
----------------------------- */
SET @i = 1;
WHILE @i <= 400000
BEGIN
    INSERT INTO OrderItems (OrderID, ProductID, Quantity, UnitPrice)
    VALUES (
        (@i % 200000) + 1,
        (@i % 1000) + 1,
        (@i % 5) + 1,
        (ABS(CHECKSUM(NEWID())) % 50000) / 100.0
    );
    SET @i += 1;
END;
GO