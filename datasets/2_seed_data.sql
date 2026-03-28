USE QueryLensDB;
GO

-- Populate Customers
SET NOCOUNT ON;

-- Customers: 50,000 rows
DECLARE @i INT = 1;
WHILE @i <= 50000
BEGIN
    INSERT INTO Customers (FirstName, LastName, Email, CreatedDate)
    VALUES (
        CONCAT('First', @i),
        CONCAT('Last', @i),
        CONCAT('user', @i, '@example.com'),
        DATEADD(DAY, -(@i % 365), GETDATE())
    );
    SET @i += 1;
END;

-- Orders: 200,000 rows
SET @i = 1;
WHILE @i <= 200000
BEGIN
    INSERT INTO Orders (CustomerID, OrderDate, OrderTotal)
    VALUES (
        (@i % 50000) + 1,
        DATEADD(DAY, -(@i % 180), GETDATE()),
        (ABS(CHECKSUM(NEWID())) % 50000) / 100.0
    );
    SET @i += 1;
END;