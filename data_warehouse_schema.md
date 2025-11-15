# Data Warehouse Schema Design

## Overview
This document defines the data warehouse schema for the analytics project using a **Star Schema** approach. The star schema is chosen for its simplicity, query performance optimization, and ease of use for business intelligence tools.

## Schema Type: Star Schema

### Why Star Schema?
- **Simplicity**: Easy to understand and navigate with clear relationships
- **Query Performance**: Optimized for OLAP queries with minimal joins
- **Denormalization**: Dimension tables are denormalized for faster reads
- **BI Tool Friendly**: Most BI tools work efficiently with star schemas

---

## Schema Diagram

```
                    ┌─────────────────────┐
                    │   dim_customers     │
                    ├─────────────────────┤
                    │ CustomerID (PK)     │
                    │ Name                │
                    │ Region              │
                    │ JoinDate            │
                    │ CreditScore         │
                    │ IndustryType        │
                    └─────────────────────┘
                              │
                              │
                              │ 1
                              │
                              │
                         ┌────┴────┐
                         │    *    │
                    ┌────▼──────────────┐
                    │   fact_sales      │
                    ├───────────────────┤
                    │ TransactionID(PK) │
                    │ CustomerID (FK)   │◄───────┐
                    │ ProductID (FK)    │        │
                    │ SaleDate          │        │
                    │ StoreID           │        │
                    │ CampaignID        │        │
                    │ SaleAmount        │        │
                    │ CommissionPercent │        │
                    │ OrderChannel      │        │
                    └───────────────────┘        │
                              │                  │
                              │ *                │
                              │                  │
                              │ 1                │
                              │                  │
                    ┌─────────▼───────────┐      │
                    │   dim_products      │      │
                    ├─────────────────────┤      │
                    │ ProductID (PK)      │──────┘
                    │ ProductName         │
                    │ Category            │
                    │ UnitPrice           │
                    │ ReorderLevel        │
                    │ StorageType         │
                    └─────────────────────┘
```

---

## Table Definitions

### 1. Fact Table: fact_sales

**Purpose**: Central fact table storing transactional sales data with measures and foreign keys to dimensions.

**Table Structure**:

| Column Name       | Data Type    | Constraints          | Description                                    |
|-------------------|--------------|----------------------|------------------------------------------------|
| TransactionID     | INTEGER      | PRIMARY KEY          | Unique identifier for each sales transaction  |
| CustomerID        | INTEGER      | FOREIGN KEY, NOT NULL| References dim_customers(CustomerID)           |
| ProductID         | INTEGER      | FOREIGN KEY, NOT NULL| References dim_products(ProductID)             |
| SaleDate          | DATE         | NOT NULL             | Date of the sale transaction                   |
| StoreID           | INTEGER      | NULL                 | Store identifier where sale occurred           |
| CampaignID        | INTEGER      | NULL                 | Marketing campaign identifier                  |
| SaleAmount        | DECIMAL(10,2)| NOT NULL             | Total sale amount (MEASURE)                    |
| CommissionPercent | DECIMAL(5,2) | NULL                 | Commission percentage (MEASURE)                |
| OrderChannel      | VARCHAR(50)  | NULL                 | Channel through which order was placed         |

**Primary Key**:
- `TransactionID`

**Foreign Keys**:
- `CustomerID` → `dim_customers(CustomerID)`
- `ProductID` → `dim_products(ProductID)`

**Indexes** (for query optimization):
```sql
-- Primary Key Index (automatically created)
CREATE INDEX idx_fact_sales_pk ON fact_sales(TransactionID);

-- Foreign Key Indexes
CREATE INDEX idx_fact_sales_customer ON fact_sales(CustomerID);
CREATE INDEX idx_fact_sales_product ON fact_sales(ProductID);

-- Date Index for time-based queries
CREATE INDEX idx_fact_sales_date ON fact_sales(SaleDate);

-- Composite Index for common query patterns
CREATE INDEX idx_fact_sales_date_customer ON fact_sales(SaleDate, CustomerID);
CREATE INDEX idx_fact_sales_date_product ON fact_sales(SaleDate, ProductID);

-- Channel Analysis Index
CREATE INDEX idx_fact_sales_channel ON fact_sales(OrderChannel);
```

**Measures** (Aggregatable Fields):
- `SaleAmount` - Sum, Average, Min, Max
- `CommissionPercent` - Average, Min, Max

**Design Considerations**:
- TransactionID serves as the grain (one row per transaction)
- Date stored in dimension-compatible format for time-series analysis
- Nullable fields (StoreID, CampaignID) allow for incomplete data
- OrderChannel stored as VARCHAR for flexible channel definitions

---

### 2. Dimension Table: dim_customers

**Purpose**: Customer dimension providing descriptive attributes about customers who make purchases.

**Table Structure**:

| Column Name   | Data Type    | Constraints          | Description                                    |
|---------------|--------------|----------------------|------------------------------------------------|
| CustomerID    | INTEGER      | PRIMARY KEY          | Unique identifier for each customer            |
| Name          | VARCHAR(100) | NOT NULL             | Customer full name                             |
| Region        | VARCHAR(50)  | NOT NULL             | Geographic region of customer                  |
| JoinDate      | DATE         | NOT NULL             | Date customer joined/registered                |
| CreditScore   | INTEGER      | NULL                 | Customer credit score (600-850 range)          |
| IndustryType  | VARCHAR(50)  | NOT NULL             | Industry sector of customer's business         |

**Primary Key**:
- `CustomerID`

**Indexes**:
```sql
-- Primary Key Index (automatically created)
CREATE INDEX idx_dim_customers_pk ON dim_customers(CustomerID);

-- Business Analysis Indexes
CREATE INDEX idx_dim_customers_region ON dim_customers(Region);
CREATE INDEX idx_dim_customers_industry ON dim_customers(IndustryType);
CREATE INDEX idx_dim_customers_join_date ON dim_customers(JoinDate);

-- Composite Index for regional industry analysis
CREATE INDEX idx_dim_customers_region_industry ON dim_customers(Region, IndustryType);
```

**Slowly Changing Dimension (SCD) Type**:
- **Type 1** (Overwrite) - Updates replace old values
- Suitable for attributes like Name, Region (assuming current state is sufficient)

**Design Considerations**:
- Denormalized structure (no further normalization of Region or IndustryType)
- CreditScore nullable to handle missing data
- Region values should be standardized during ETL process
- IndustryType provides business segmentation capability

---

### 3. Dimension Table: dim_products

**Purpose**: Product dimension providing descriptive attributes about products sold.

**Table Structure**:

| Column Name   | Data Type     | Constraints          | Description                                    |
|---------------|---------------|----------------------|------------------------------------------------|
| ProductID     | INTEGER       | PRIMARY KEY          | Unique identifier for each product             |
| ProductName   | VARCHAR(100)  | NOT NULL             | Name/description of the product                |
| Category      | VARCHAR(50)   | NOT NULL             | Product category classification                |
| UnitPrice     | DECIMAL(10,2) | NOT NULL             | Standard unit price of the product             |
| ReorderLevel  | INTEGER       | NOT NULL             | Inventory reorder threshold level              |
| StorageType   | VARCHAR(50)   | NOT NULL             | Type of storage required (Warehouse/Retail)    |

**Primary Key**:
- `ProductID`

**Indexes**:
```sql
-- Primary Key Index (automatically created)
CREATE INDEX idx_dim_products_pk ON dim_products(ProductID);

-- Category Analysis Index
CREATE INDEX idx_dim_products_category ON dim_products(Category);

-- Storage Type Index
CREATE INDEX idx_dim_products_storage ON dim_products(StorageType);

-- Price Range Analysis Index
CREATE INDEX idx_dim_products_price ON dim_products(UnitPrice);

-- Composite Index for category-price analysis
CREATE INDEX idx_dim_products_cat_price ON dim_products(Category, UnitPrice);
```

**Slowly Changing Dimension (SCD) Type**:
- **Type 1** (Overwrite) for most attributes (ProductName, StorageType, ReorderLevel)
- **Type 2** (Historical) consideration for UnitPrice if price history tracking is needed

**Design Considerations**:
- Denormalized structure (Category stored directly without separate category table)
- UnitPrice represents standard price; actual sale price is in fact table
- ReorderLevel supports inventory management queries
- StorageType enables logistics and warehouse analysis

---

## Relationships

### Cardinality

1. **dim_customers to fact_sales**: One-to-Many (1:N)
   - One customer can have many sales transactions
   - Each sale transaction is associated with exactly one customer

2. **dim_products to fact_sales**: One-to-Many (1:N)
   - One product can appear in many sales transactions
   - Each sale transaction is associated with exactly one product

### Referential Integrity

- **Foreign Key Constraints** enforce referential integrity
- **ON DELETE RESTRICT** prevents deletion of dimension records with existing fact references
- **ON UPDATE CASCADE** allows dimension key updates to propagate to fact table

---

## Query Performance Optimization

### Indexing Strategy

1. **Fact Table Indexes**:
   - Primary key on TransactionID
   - Foreign key indexes on CustomerID and ProductID
   - Date-based indexes for time-series analysis
   - Composite indexes for common join patterns

2. **Dimension Table Indexes**:
   - Primary key indexes
   - Indexes on frequently filtered attributes (Region, Category, IndustryType)
   - Composite indexes for multi-attribute queries

### Partitioning Considerations

For large datasets, consider:
- **Partitioning fact_sales by SaleDate** (monthly or quarterly partitions)
- Improves query performance for time-based analysis
- Facilitates easier data archival and maintenance

### Materialized Views

Consider creating materialized views for:
- Monthly/Quarterly sales aggregations
- Customer lifetime value calculations
- Product category performance summaries

---

## Data Integrity Rules

### Business Rules

1. **Fact Table**:
   - SaleAmount must be >= 0
   - CommissionPercent must be between 0 and 100
   - SaleDate must be <= current date
   - CustomerID and ProductID must exist in respective dimension tables

2. **Dimension Tables**:
   - CustomerID and ProductID must be unique
   - CreditScore (when present) must be between 300 and 850
   - UnitPrice must be > 0
   - ReorderLevel must be >= 0

### Constraints

```sql
-- Fact Table Constraints
ALTER TABLE fact_sales
    ADD CONSTRAINT chk_sale_amount CHECK (SaleAmount >= 0),
    ADD CONSTRAINT chk_commission CHECK (CommissionPercent >= 0 AND CommissionPercent <= 100),
    ADD CONSTRAINT chk_sale_date CHECK (SaleDate <= CURRENT_DATE);

-- Customer Dimension Constraints
ALTER TABLE dim_customers
    ADD CONSTRAINT chk_credit_score CHECK (CreditScore IS NULL OR (CreditScore >= 300 AND CreditScore <= 850));

-- Product Dimension Constraints
ALTER TABLE dim_products
    ADD CONSTRAINT chk_unit_price CHECK (UnitPrice > 0),
    ADD CONSTRAINT chk_reorder_level CHECK (ReorderLevel >= 0);
```

---

## ETL Considerations

### Data Loading Strategy

1. **Dimension Tables** (Load First):
   - Load dim_customers
   - Load dim_products
   - Ensure dimension keys are established before fact loading

2. **Fact Table** (Load Second):
   - Load fact_sales
   - Validate foreign key references
   - Handle orphaned records (sales without valid customer/product)

### Data Quality Checks

- **Pre-load validation**: Check for missing required fields
- **Referential integrity**: Verify CustomerID and ProductID exist in dimensions
- **Data type validation**: Ensure numeric fields contain valid numbers
- **Duplicate detection**: Check for duplicate TransactionIDs
- **Date validation**: Verify date formats and reasonable date ranges

---

## Sample SQL DDL

```sql
-- Create Customers Dimension Table
CREATE TABLE dim_customers (
    CustomerID INTEGER PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Region VARCHAR(50) NOT NULL,
    JoinDate DATE NOT NULL,
    CreditScore INTEGER,
    IndustryType VARCHAR(50) NOT NULL,
    CONSTRAINT chk_credit_score CHECK (CreditScore IS NULL OR (CreditScore >= 300 AND CreditScore <= 850))
);

-- Create Products Dimension Table
CREATE TABLE dim_products (
    ProductID INTEGER PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    Category VARCHAR(50) NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    ReorderLevel INTEGER NOT NULL,
    StorageType VARCHAR(50) NOT NULL,
    CONSTRAINT chk_unit_price CHECK (UnitPrice > 0),
    CONSTRAINT chk_reorder_level CHECK (ReorderLevel >= 0)
);

-- Create Sales Fact Table
CREATE TABLE fact_sales (
    TransactionID INTEGER PRIMARY KEY,
    CustomerID INTEGER NOT NULL,
    ProductID INTEGER NOT NULL,
    SaleDate DATE NOT NULL,
    StoreID INTEGER,
    CampaignID INTEGER,
    SaleAmount DECIMAL(10,2) NOT NULL,
    CommissionPercent DECIMAL(5,2),
    OrderChannel VARCHAR(50),
    CONSTRAINT fk_customer FOREIGN KEY (CustomerID) REFERENCES dim_customers(CustomerID) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_product FOREIGN KEY (ProductID) REFERENCES dim_products(ProductID) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_sale_amount CHECK (SaleAmount >= 0),
    CONSTRAINT chk_commission CHECK (CommissionPercent >= 0 AND CommissionPercent <= 100),
    CONSTRAINT chk_sale_date CHECK (SaleDate <= CURRENT_DATE)
);

-- Create Indexes for Fact Table
CREATE INDEX idx_fact_sales_customer ON fact_sales(CustomerID);
CREATE INDEX idx_fact_sales_product ON fact_sales(ProductID);
CREATE INDEX idx_fact_sales_date ON fact_sales(SaleDate);
CREATE INDEX idx_fact_sales_date_customer ON fact_sales(SaleDate, CustomerID);
CREATE INDEX idx_fact_sales_date_product ON fact_sales(SaleDate, ProductID);
CREATE INDEX idx_fact_sales_channel ON fact_sales(OrderChannel);

-- Create Indexes for Dimension Tables
CREATE INDEX idx_dim_customers_region ON dim_customers(Region);
CREATE INDEX idx_dim_customers_industry ON dim_customers(IndustryType);
CREATE INDEX idx_dim_customers_join_date ON dim_customers(JoinDate);
CREATE INDEX idx_dim_customers_region_industry ON dim_customers(Region, IndustryType);

CREATE INDEX idx_dim_products_category ON dim_products(Category);
CREATE INDEX idx_dim_products_storage ON dim_products(StorageType);
CREATE INDEX idx_dim_products_price ON dim_products(UnitPrice);
CREATE INDEX idx_dim_products_cat_price ON dim_products(Category, UnitPrice);
```

---

## Common Query Patterns

### 1. Total Sales by Customer Region
```sql
SELECT
    c.Region,
    COUNT(DISTINCT f.TransactionID) AS TotalTransactions,
    SUM(f.SaleAmount) AS TotalSales,
    AVG(f.SaleAmount) AS AvgSaleAmount
FROM fact_sales f
JOIN dim_customers c ON f.CustomerID = c.CustomerID
GROUP BY c.Region
ORDER BY TotalSales DESC;
```

### 2. Product Category Performance
```sql
SELECT
    p.Category,
    COUNT(DISTINCT f.TransactionID) AS TransactionCount,
    SUM(f.SaleAmount) AS TotalRevenue,
    AVG(f.CommissionPercent) AS AvgCommission
FROM fact_sales f
JOIN dim_products p ON f.ProductID = p.ProductID
GROUP BY p.Category
ORDER BY TotalRevenue DESC;
```

### 3. Time-Series Sales Analysis
```sql
SELECT
    DATE_TRUNC('month', f.SaleDate) AS SaleMonth,
    SUM(f.SaleAmount) AS MonthlyRevenue,
    COUNT(DISTINCT f.CustomerID) AS UniqueCustomers,
    COUNT(DISTINCT f.TransactionID) AS TotalTransactions
FROM fact_sales f
WHERE f.SaleDate >= DATE_TRUNC('year', CURRENT_DATE)
GROUP BY DATE_TRUNC('month', f.SaleDate)
ORDER BY SaleMonth;
```

### 4. Customer Industry Analysis
```sql
SELECT
    c.IndustryType,
    c.Region,
    COUNT(DISTINCT c.CustomerID) AS CustomerCount,
    SUM(f.SaleAmount) AS TotalSales,
    AVG(c.CreditScore) AS AvgCreditScore
FROM dim_customers c
LEFT JOIN fact_sales f ON c.CustomerID = f.CustomerID
GROUP BY c.IndustryType, c.Region
ORDER BY TotalSales DESC;
```

---

## Schema Maintenance

### Regular Maintenance Tasks

1. **Index Maintenance**:
   - Rebuild fragmented indexes monthly
   - Update statistics weekly for query optimization

2. **Data Archival**:
   - Archive fact_sales records older than specified retention period
   - Maintain dimension history if using SCD Type 2

3. **Performance Monitoring**:
   - Monitor query execution times
   - Identify and optimize slow-running queries
   - Review and adjust indexes based on query patterns

### Schema Evolution

- **Adding new dimensions**: Create new dimension table and add FK to fact table
- **Adding new measures**: Add columns to fact table
- **Adding new attributes**: Add columns to dimension tables
- **Version control**: Document all schema changes with migration scripts

---

## Summary

This star schema design provides:

✅ **Optimized Query Performance**: Minimal joins and indexed foreign keys
✅ **Data Integrity**: Enforced through primary keys, foreign keys, and constraints
✅ **Scalability**: Partitioning and indexing strategies support growth
✅ **Business Intelligence**: Clear relationships for reporting and analytics
✅ **Maintainability**: Simple structure with documented patterns

**Next Steps**:
1. Implement DDL scripts in target database
2. Develop ETL processes to populate tables
3. Create data quality validation procedures
4. Build reporting views and aggregations
