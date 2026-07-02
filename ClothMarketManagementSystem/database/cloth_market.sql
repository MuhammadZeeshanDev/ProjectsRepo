-- ==============================================================
-- CLOTH MARKET MANAGEMENT SYSTEM
-- Database : Microsoft SQL Server 2022
-- Course   : CT-261 Database Management Systems
-- ==============================================================

IF DB_ID('ClothMarketDB') IS NULL
BEGIN
    CREATE DATABASE ClothMarketDB;
END
GO
USE ClothMarketDB;
GO

-- Drop in dependency order so this script can be re-run safely.
IF OBJECT_ID('dbo.Orders', 'U') IS NOT NULL DROP TABLE dbo.Orders;
IF OBJECT_ID('dbo.Customer', 'U') IS NOT NULL DROP TABLE dbo.Customer;
IF OBJECT_ID('dbo.Supplier', 'U') IS NOT NULL DROP TABLE dbo.Supplier;
IF OBJECT_ID('dbo.Fabric', 'U')   IS NOT NULL DROP TABLE dbo.Fabric;
IF OBJECT_ID('dbo.Shop', 'U')     IS NOT NULL DROP TABLE dbo.Shop;
GO

-- TABLE 1: CUSTOMER
CREATE TABLE Customer (
    Customer_ID   INT IDENTITY(1,1) PRIMARY KEY,
    Customer_Name VARCHAR(100) NOT NULL,
    Phone         VARCHAR(20)  NOT NULL UNIQUE,
    City          VARCHAR(50)  NOT NULL
);
GO

-- TABLE 2: SUPPLIER
CREATE TABLE Supplier (
    Supplier_ID   INT IDENTITY(1,1) PRIMARY KEY,
    Supplier_Name VARCHAR(100) NOT NULL,
    Phone         VARCHAR(20)  NOT NULL UNIQUE,
    City          VARCHAR(50)  NOT NULL
);
GO

-- TABLE 3: FABRIC
CREATE TABLE Fabric (
    Fabric_ID       INT IDENTITY(1,1) PRIMARY KEY,
    Fabric_Name     VARCHAR(100)  NOT NULL,
    Category        VARCHAR(50)   NOT NULL,
    Price_Per_Meter DECIMAL(10,2) NOT NULL CHECK (Price_Per_Meter > 0)
);
GO

-- TABLE 4: SHOP
CREATE TABLE Shop (
    Shop_ID    INT IDENTITY(1,1) PRIMARY KEY,
    Shop_Name  VARCHAR(100) NOT NULL,
    Owner_Name VARCHAR(100) NOT NULL,
    Phone      VARCHAR(20)  NOT NULL,
    Location   VARCHAR(150) NOT NULL,
    City       VARCHAR(50)  NOT NULL
);
GO

-- TABLE 5: ORDERS
CREATE TABLE Orders (
    Order_ID         INT IDENTITY(1,1) PRIMARY KEY,
    Order_Date       DATE          NOT NULL DEFAULT GETDATE(),
    Customer_ID      INT           NOT NULL,
    Shop_ID          INT           NOT NULL,
    Fabric_ID        INT           NOT NULL,
    Supplier_ID      INT           NOT NULL,
    Quantity_Meters  INT           NOT NULL CHECK (Quantity_Meters > 0),
    Price_Per_Meter  DECIMAL(10,2) NOT NULL,
    Discount_Percent INT           NOT NULL DEFAULT 0
        CHECK (Discount_Percent >= 0 AND Discount_Percent <= 100),
    Total_Amount     DECIMAL(10,2) NOT NULL,
    Payment_Method   VARCHAR(30)   NOT NULL
        CHECK (Payment_Method IN ('Cash','Bank Transfer','Cheque','Online Payment')),
    Payment_Status   VARCHAR(20)   NOT NULL
        CHECK (Payment_Status IN ('Paid','Unpaid','Partial')),
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID),
    FOREIGN KEY (Shop_ID)     REFERENCES Shop(Shop_ID),
    FOREIGN KEY (Fabric_ID)   REFERENCES Fabric(Fabric_ID),
    FOREIGN KEY (Supplier_ID) REFERENCES Supplier(Supplier_ID)
);
GO

-- ==============================================================
-- SAMPLE DATA
-- ==============================================================

INSERT INTO Customer (Customer_Name, Phone, City) VALUES
('Ahmed Ali',        '0312-1111111', 'Karachi'),
('Muhammad Usman',   '0321-2222222', 'Lahore'),
('Fatima Zahra',     '0333-3333333', 'Islamabad'),
('Ali Hassan',       '0300-4444444', 'Karachi'),
('Sara Khan',        '0345-5555555', 'Faisalabad'),
('Zainab Malik',     '0311-6666666', 'Karachi'),
('Bilal Ahmed',      '0322-7777777', 'Lahore'),
('Ayesha Siddiqui',  '0301-8888888', 'Multan'),
('Omar Farooq',      '0334-9999999', 'Karachi'),
('Hina Baig',        '0344-1010101', 'Peshawar');
GO

INSERT INTO Supplier (Supplier_Name, Phone, City) VALUES
('Gul Ahmed Textile',  '0321-1234567', 'Karachi'),
('Al-Karam Studio',    '0300-2345678', 'Lahore'),
('Nishat Linen',       '0333-3456789', 'Faisalabad'),
('Khaadi Textiles',    '0322-7890123', 'Karachi'),
('Sapphire Fabrics',   '0345-5678901', 'Lahore');
GO

INSERT INTO Fabric (Fabric_Name, Category, Price_Per_Meter) VALUES
('Lawn',        'Summer Fabric',  350.00),
('Khaddar',     'Winter Fabric',  450.00),
('Silk',        'Premium Fabric', 1800.00),
('Chiffon',     'Party Fabric',   650.00),
('Cotton',      'Casual Fabric',  300.00),
('Velvet',      'Winter Fabric',  1200.00),
('Georgette',   'Party Fabric',   550.00),
('Linen',       'Casual Fabric',  600.00);
GO

INSERT INTO Shop (Shop_Name, Owner_Name, Phone, Location, City) VALUES
('Bismillah Fabrics',      'Haji Abdul Rehman', '0312-0011001', 'Shop 14, Jodia Bazaar',         'Karachi'),
('Al-Madina Cloth House',  'Muhammad Tariq',    '0321-0022002', 'Shop 7, Bohri Bazaar',           'Karachi'),
('New Style Fabrics',      'Arif Hussain',      '0300-0033003', 'Shop 22, Liberty Market',        'Lahore'),
('Pak Cloth Center',       'Naveed Akhtar',     '0345-0044004', 'Shop 5, Anarkali Bazaar',        'Lahore'),
('Zainab Cloth Store',     'Rashid Mehmood',    '0333-0055005', 'Shop 9, Zainab Market',          'Karachi'),
('Crown Fabrics',          'Khalid Pervaiz',    '0311-0066006', 'Shop 3, Faisalabad Cloth Market','Faisalabad');
GO

INSERT INTO Orders (Order_Date, Customer_ID, Shop_ID, Fabric_ID, Supplier_ID,
                    Quantity_Meters, Price_Per_Meter, Discount_Percent,
                    Total_Amount, Payment_Method, Payment_Status) VALUES
('2024-01-05', 1, 1, 1, 1, 20, 350.00, 0,  7000.00,  'Cash',           'Paid'),
('2024-01-10', 2, 3, 2, 2, 15, 450.00, 5,  6412.50,  'Bank Transfer',  'Paid'),
('2024-01-15', 3, 3, 3, 3, 10, 1800.00,10, 16200.00, 'Cheque',         'Partial'),
('2024-02-01', 4, 1, 4, 4, 25, 650.00, 0,  16250.00, 'Cash',           'Paid'),
('2024-02-14', 5, 4, 5, 5, 30, 300.00, 5,  8550.00,  'Online Payment', 'Unpaid'),
('2024-02-20', 1, 2, 1, 1, 40, 350.00, 0,  14000.00, 'Cash',           'Paid'),
('2024-03-01', 2, 3, 2, 2, 20, 450.00, 10, 8100.00,  'Bank Transfer',  'Paid'),
('2024-03-05', 6, 2, 6, 1, 8,  1200.00,15, 8160.00,  'Cheque',         'Paid'),
('2024-03-10', 7, 4, 3, 3, 5,  1800.00,0,  9000.00,  'Cash',           'Unpaid'),
('2024-03-15', 8, 1, 1, 4, 50, 350.00, 5,  16625.00, 'Online Payment', 'Paid');
GO
