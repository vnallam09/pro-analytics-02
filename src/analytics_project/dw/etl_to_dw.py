"""ETL script to create and populate the data warehouse with star schema.

This module implements the Extract, Transform, Load (ETL) process to:
1. Create the data warehouse schema (star schema) in SQLite
2. Load dimension tables (customers, products)
3. Load fact table (sales)

The star schema consists of:
- dim_customers: Customer dimension table
- dim_products: Product dimension table
- fact_sales: Sales fact table with foreign keys to dimensions

Module Information:
    - Filename: etl_to_dw.py
    - Module: etl_to_dw
    - Location: src/analytics_project/

Key Concepts:
    - Star Schema Design
    - Data Warehouse ETL
    - Dimension and Fact Tables
    - Foreign Key Relationships
    - Data Integrity and Validation

Business Value:
    - Centralized data repository for analytics
    - Optimized query performance for business intelligence
    - Consistent data model for reporting
    - Referential integrity enforcement
"""

import csv
import pathlib
import sqlite3
from typing import Any

from analytics_project.utils_logger import logger

# ============================================================================
# Configuration
# ============================================================================

# Project root is three levels up from this file (dw folder added)
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
DATA_PREPARED = PROJECT_ROOT / "data" / "prepared"
DW_DATABASE = PROJECT_ROOT / "data_warehouse.db"

# Prepared data file paths
CUSTOMERS_PREPARED = DATA_PREPARED / "customers_prepared.csv"
PRODUCTS_PREPARED = DATA_PREPARED / "products_prepared.csv"
SALES_PREPARED = DATA_PREPARED / "sales_prepared.csv"


# ============================================================================
# SQL DDL Statements - Data Warehouse Schema
# ============================================================================

# Create Customers Dimension Table
CREATE_DIM_CUSTOMERS = """
CREATE TABLE IF NOT EXISTS dim_customers (
    CustomerID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL,
    Region TEXT NOT NULL,
    JoinDate TEXT NOT NULL,
    CreditScore REAL,
    IndustryType TEXT NOT NULL
);
"""

# Create Products Dimension Table
CREATE_DIM_PRODUCTS = """
CREATE TABLE IF NOT EXISTS dim_products (
    ProductID INTEGER PRIMARY KEY,
    ProductName TEXT NOT NULL,
    Category TEXT NOT NULL,
    UnitPrice REAL NOT NULL CHECK (UnitPrice > 0),
    ReorderLevel INTEGER NOT NULL CHECK (ReorderLevel >= 0),
    StorageType TEXT NOT NULL
);
"""

# Create Sales Fact Table
CREATE_FACT_SALES = """
CREATE TABLE IF NOT EXISTS fact_sales (
    TransactionID INTEGER PRIMARY KEY,
    CustomerID INTEGER NOT NULL,
    ProductID INTEGER NOT NULL,
    SaleDate TEXT NOT NULL,
    StoreID INTEGER,
    CampaignID REAL,
    SaleAmount REAL NOT NULL CHECK (SaleAmount >= 0),
    CommissionPercent REAL CHECK (CommissionPercent >= 0 AND CommissionPercent <= 100),
    OrderChannel TEXT,
    FOREIGN KEY (CustomerID) REFERENCES dim_customers(CustomerID) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (ProductID) REFERENCES dim_products(ProductID) ON DELETE RESTRICT ON UPDATE CASCADE
);
"""

# Create Indexes for Query Performance
CREATE_INDEXES = [
    # Fact table indexes
    "CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON fact_sales(CustomerID);",
    "CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON fact_sales(ProductID);",
    "CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales(SaleDate);",
    "CREATE INDEX IF NOT EXISTS idx_fact_sales_channel ON fact_sales(OrderChannel);",
    # Dimension table indexes
    "CREATE INDEX IF NOT EXISTS idx_dim_customers_region ON dim_customers(Region);",
    "CREATE INDEX IF NOT EXISTS idx_dim_customers_industry ON dim_customers(IndustryType);",
    "CREATE INDEX IF NOT EXISTS idx_dim_products_category ON dim_products(Category);",
    "CREATE INDEX IF NOT EXISTS idx_dim_products_storage ON dim_products(StorageType);",
]


# ============================================================================
# Database Connection Management
# ============================================================================


def create_database_connection(db_path: pathlib.Path) -> sqlite3.Connection:
    """Create and return a SQLite database connection.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        sqlite3.Connection: Database connection object

    Raises:
        sqlite3.Error: If connection fails
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key support
        logger.info(f"Connected to database: {db_path}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database {db_path}: {e}")
        raise


# ============================================================================
# Schema Creation Functions
# ============================================================================


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the data warehouse schema (tables and indexes).

    Creates dimension tables first, then fact table, then indexes
    to ensure referential integrity.

    Args:
        conn: SQLite database connection

    Raises:
        sqlite3.Error: If schema creation fails
    """
    cursor = conn.cursor()

    try:
        logger.info("Creating data warehouse schema...")

        # Create dimension tables first (no dependencies)
        logger.info("Creating dim_customers table...")
        cursor.execute(CREATE_DIM_CUSTOMERS)

        logger.info("Creating dim_products table...")
        cursor.execute(CREATE_DIM_PRODUCTS)

        # Create fact table (depends on dimensions)
        logger.info("Creating fact_sales table...")
        cursor.execute(CREATE_FACT_SALES)

        # Create indexes for query optimization
        logger.info("Creating indexes...")
        for idx, create_index_sql in enumerate(CREATE_INDEXES, 1):
            cursor.execute(create_index_sql)
            logger.debug(f"Created index {idx}/{len(CREATE_INDEXES)}")

        conn.commit()
        logger.success("Data warehouse schema created successfully!")

    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Failed to create schema: {e}")
        raise


# ============================================================================
# Data Loading Functions
# ============================================================================


def load_customers_dimension(conn: sqlite3.Connection, csv_path: pathlib.Path) -> int:
    """Load customer data into dim_customers table.

    Args:
        conn: SQLite database connection
        csv_path: Path to customers_prepared.csv file

    Returns:
        int: Number of records inserted

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        sqlite3.Error: If data loading fails
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Customer data file not found: {csv_path}")

    cursor = conn.cursor()
    records_inserted = 0

    try:
        logger.info(f"Loading customers from {csv_path.name}...")

        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            for row in csv_reader:
                # Handle 'Unknown' credit scores
                credit_score = (
                    None if row['CreditScore'] == 'Unknown' else float(row['CreditScore'])
                )

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO dim_customers
                    (CustomerID, Name, Region, JoinDate, CreditScore, IndustryType)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        int(row['CustomerID']),
                        row['Name'],
                        row['Region'],
                        row['JoinDate'],
                        credit_score,
                        row['IndustryType'],
                    ),
                )
                records_inserted += 1

        conn.commit()
        logger.success(f"Loaded {records_inserted} customer records into dim_customers")
        return records_inserted

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to load customer data: {e}")
        raise


def load_products_dimension(conn: sqlite3.Connection, csv_path: pathlib.Path) -> int:
    """Load product data into dim_products table.

    Args:
        conn: SQLite database connection
        csv_path: Path to products_prepared.csv file

    Returns:
        int: Number of records inserted

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        sqlite3.Error: If data loading fails
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Product data file not found: {csv_path}")

    cursor = conn.cursor()
    records_inserted = 0

    try:
        logger.info(f"Loading products from {csv_path.name}...")

        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            for row in csv_reader:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO dim_products
                    (ProductID, ProductName, Category, UnitPrice, ReorderLevel, StorageType)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        int(row['ProductID']),
                        row['ProductName'],
                        row['Category'],
                        float(row['UnitPrice']),
                        int(float(row['ReorderLevel'])),
                        row['StorageType'],
                    ),
                )
                records_inserted += 1

        conn.commit()
        logger.success(f"Loaded {records_inserted} product records into dim_products")
        return records_inserted

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to load product data: {e}")
        raise


def load_sales_fact(conn: sqlite3.Connection, csv_path: pathlib.Path) -> tuple[int, int]:
    """Load sales data into fact_sales table.

    Only loads sales records where both CustomerID and ProductID exist
    in their respective dimension tables (referential integrity).

    Args:
        conn: SQLite database connection
        csv_path: Path to sales_prepared.csv file

    Returns:
        tuple[int, int]: (records_inserted, records_skipped)

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        sqlite3.Error: If data loading fails
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Sales data file not found: {csv_path}")

    cursor = conn.cursor()
    records_inserted = 0
    records_skipped = 0

    try:
        logger.info(f"Loading sales from {csv_path.name}...")

        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            for row in csv_reader:
                try:
                    # Convert CampaignID to None if empty
                    campaign_id = (
                        None
                        if not row['CampaignID'] or row['CampaignID'] == ''
                        else float(row['CampaignID'])
                    )

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO fact_sales
                        (TransactionID, CustomerID, ProductID, SaleDate, StoreID,
                         CampaignID, SaleAmount, CommissionPercent, OrderChannel)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            int(row['TransactionID']),
                            int(row['CustomerID']),
                            int(row['ProductID']),
                            row['SaleDate'],
                            int(row['StoreID']),
                            campaign_id,
                            float(row['SaleAmount']),
                            float(row['CommissionPercent']),
                            row['OrderChannel'],
                        ),
                    )
                    records_inserted += 1

                except sqlite3.IntegrityError as ie:
                    # Foreign key constraint violation or orphaned record
                    logger.warning(f"Skipping transaction {row['TransactionID']}: {ie}")
                    records_skipped += 1
                    continue

        conn.commit()
        logger.success(f"Loaded {records_inserted} sales records into fact_sales")
        if records_skipped > 0:
            logger.warning(f"Skipped {records_skipped} records due to referential integrity issues")
        return records_inserted, records_skipped

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to load sales data: {e}")
        raise


# ============================================================================
# Data Validation Functions
# ============================================================================


def validate_data_warehouse(conn: sqlite3.Connection) -> dict[str, Any]:
    """Validate the data warehouse after loading.

    Performs various checks to ensure data integrity and quality.

    Args:
        conn: SQLite database connection

    Returns:
        dict: Validation statistics including record counts and integrity checks
    """
    cursor = conn.cursor()
    stats = {}

    try:
        logger.info("Validating data warehouse...")

        # Count records in each table
        cursor.execute("SELECT COUNT(*) FROM dim_customers")
        stats['customers_count'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dim_products")
        stats['products_count'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM fact_sales")
        stats['sales_count'] = cursor.fetchone()[0]

        # Check for orphaned sales records (should be none with FK constraints)
        cursor.execute("""
            SELECT COUNT(*)
            FROM fact_sales f
            LEFT JOIN dim_customers c ON f.CustomerID = c.CustomerID
            WHERE c.CustomerID IS NULL
        """)
        stats['orphaned_customers'] = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM fact_sales f
            LEFT JOIN dim_products p ON f.ProductID = p.ProductID
            WHERE p.ProductID IS NULL
        """)
        stats['orphaned_products'] = cursor.fetchone()[0]

        # Calculate total sales amount
        cursor.execute("SELECT SUM(SaleAmount) FROM fact_sales")
        stats['total_sales_amount'] = cursor.fetchone()[0] or 0.0

        # Count sales by channel
        cursor.execute("""
            SELECT OrderChannel, COUNT(*)
            FROM fact_sales
            GROUP BY OrderChannel
        """)
        stats['sales_by_channel'] = dict(cursor.fetchall())

        logger.success("Data warehouse validation complete!")
        logger.info(f"Customers: {stats['customers_count']}")
        logger.info(f"Products: {stats['products_count']}")
        logger.info(f"Sales Transactions: {stats['sales_count']}")
        logger.info(f"Total Sales Amount: ${stats['total_sales_amount']:,.2f}")
        logger.info(f"Orphaned Customer References: {stats['orphaned_customers']}")
        logger.info(f"Orphaned Product References: {stats['orphaned_products']}")

        return stats

    except sqlite3.Error as e:
        logger.error(f"Validation failed: {e}")
        raise


# ============================================================================
# Main ETL Pipeline
# ============================================================================


def run_etl_pipeline() -> None:
    """Execute the complete ETL pipeline to build the data warehouse.

    Steps:
    1. Create database connection
    2. Create schema (tables and indexes)
    3. Load dimension tables (customers, products)
    4. Load fact table (sales)
    5. Validate data warehouse
    6. Close connection

    Raises:
        Exception: If any step of the ETL pipeline fails
    """
    conn = None

    try:
        logger.info("=" * 70)
        logger.info("Starting Data Warehouse ETL Pipeline")
        logger.info("=" * 70)

        # Step 1: Create database connection
        conn = create_database_connection(DW_DATABASE)

        # Step 2: Create schema
        create_schema(conn)

        # Step 3: Load dimension tables (must load before fact table)
        logger.info("-" * 70)
        logger.info("Loading Dimension Tables")
        logger.info("-" * 70)

        customers_loaded = load_customers_dimension(conn, CUSTOMERS_PREPARED)
        products_loaded = load_products_dimension(conn, PRODUCTS_PREPARED)

        # Step 4: Load fact table
        logger.info("-" * 70)
        logger.info("Loading Fact Table")
        logger.info("-" * 70)

        sales_loaded, sales_skipped = load_sales_fact(conn, SALES_PREPARED)

        # Step 5: Validate data warehouse
        logger.info("-" * 70)
        logger.info("Validating Data Warehouse")
        logger.info("-" * 70)

        validation_stats = validate_data_warehouse(conn)

        # Summary
        logger.info("=" * 70)
        logger.info("ETL Pipeline Summary")
        logger.info("=" * 70)
        logger.info(f"Database Location: {DW_DATABASE}")
        logger.info(f"Customers Loaded: {customers_loaded}")
        logger.info(f"Products Loaded: {products_loaded}")
        logger.info(f"Sales Loaded: {sales_loaded}")
        logger.info(f"Sales Skipped: {sales_skipped}")
        logger.success("ETL Pipeline completed successfully! 🎉")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"ETL Pipeline failed: {e}")
        raise

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")


# ============================================================================
# Script Entry Point
# ============================================================================


def main() -> None:
    """Main entry point for the ETL script."""
    from analytics_project import utils_logger

    # Initialize logging
    utils_logger.init_logger()

    # Run the ETL pipeline
    run_etl_pipeline()


if __name__ == "__main__":
    main()
