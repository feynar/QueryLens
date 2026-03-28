-- QueryLens baseline schema for execution plan analysis
-- SQL Server 2019+

CREATE DATABASE QueryLensDB;
GO
USE QueryLensDB;
GO

CREATE TABLE Customers (
    CustomerID INT IDENTITY PRIMARY KEY,
    FirstName NVARCHAR(50),
    LastName NVARCHAR(50),
    Email NVARCHAR(100),
    CreatedDate DATE
);

CREATE TABLE Orders (
    OrderID INT IDENTITY PRIMARY KEY,
    CustomerID INT NOT NULL,
    OrderDate DATE,
    OrderTotal DECIMAL(10,2),
    CONSTRAINT FK_Orders_Customers FOREIGN KEY (CustomerID)
        REFERENCES Customers(CustomerID)
);

-- Indexes to influence execution plans
CREATE INDEX IX_Customers_CreatedDate ON Customers(CreatedDate);
CREATE INDEX IX_Orders_CustomerID ON Orders(CustomerID);
CREATE INDEX IX_Orders_OrderDate ON Orders(OrderDate);
GO
