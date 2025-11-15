"""Validate the data warehouse schema and data integrity.

This module performs comprehensive validation of the data warehouse including:
- Schema structure verification
- Data integrity checks
- Sample queries to demonstrate functionality
- Relationship validation

Module Information:
    - Filename: validate_dw.py
    - Module: validate_dw
    - Location: src/analytics_project/dw/

Key Validation Checks:
    - Table existence and structure
    - Record counts
    - Foreign key relationships
    - Data quality metrics
    - Sample analytical queries
"""

import pathlib
import sqlite3
from typing import Any

from analytics_project.utils_logger import logger

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
DW_DATABASE = PROJECT_ROOT / "data_warehouse.db"


# ============================================================================
# Database Connection
# ============================================================================


def create_connection() -> sqlite3.Connection:
    """Create and return a database connection.

    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        conn = sqlite3.connect(DW_DATABASE)
        conn.row_factory = sqlite3.Row  # Access columns by name
        logger.info(f"Connected to database: {DW_DATABASE}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


# ============================================================================
# Schema Validation Functions
# ============================================================================


def validate_table_structure(conn: sqlite3.Connection) -> dict[str, Any]:
    """Validate the structure of all tables in the data warehouse.

    Args:
        conn: Database connection

    Returns:
        dict: Table structure information
    """
    cursor = conn.cursor()
    tables = {}

    logger.info("=" * 70)
    logger.info("VALIDATING TABLE STRUCTURES")
    logger.info("=" * 70)

    # Get all tables
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    table_names = [row[0] for row in cursor.fetchall()]

    for table_name in table_names:
        logger.info(f"\n📊 Table: {table_name}")
        logger.info("-" * 70)

        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        table_info = {"columns": [], "primary_keys": [], "foreign_keys": []}

        # Display columns
        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            table_info["columns"].append(
                {
                    "name": name,
                    "type": col_type,
                    "not_null": bool(not_null),
                    "primary_key": bool(pk),
                }
            )

            pk_marker = " [PK]" if pk else ""
            null_marker = " NOT NULL" if not_null else ""
            logger.info(f"  • {name:<20} {col_type:<15}{null_marker}{pk_marker}")

            if pk:
                table_info["primary_keys"].append(name)

        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = cursor.fetchall()

        if fks:
            logger.info("\n  Foreign Keys:")
            for fk in fks:
                fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                logger.info(f"    → {from_col} references {ref_table}({to_col})")
                table_info["foreign_keys"].append(
                    {"column": from_col, "references_table": ref_table, "references_column": to_col}
                )

        # Get indexes
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()

        if indexes:
            logger.info("\n  Indexes:")
            for idx in indexes:
                seq, name, unique, origin, partial = idx
                logger.info(f"    • {name}")

        tables[table_name] = table_info

    return tables


def validate_record_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Validate record counts in all tables.

    Args:
        conn: Database connection

    Returns:
        dict: Record counts by table
    """
    cursor = conn.cursor()
    counts = {}

    logger.info("\n" + "=" * 70)
    logger.info("VALIDATING RECORD COUNTS")
    logger.info("=" * 70)

    # Dimension tables
    cursor.execute("SELECT COUNT(*) FROM dim_customers")
    counts["dim_customers"] = cursor.fetchone()[0]
    logger.info(f"📊 dim_customers: {counts['dim_customers']:,} records")

    cursor.execute("SELECT COUNT(*) FROM dim_products")
    counts["dim_products"] = cursor.fetchone()[0]
    logger.info(f"📦 dim_products: {counts['dim_products']:,} records")

    # Fact table
    cursor.execute("SELECT COUNT(*) FROM fact_sales")
    counts["fact_sales"] = cursor.fetchone()[0]
    logger.info(f"💰 fact_sales: {counts['fact_sales']:,} records")

    return counts


def validate_referential_integrity(conn: sqlite3.Connection) -> dict[str, Any]:
    """Validate referential integrity between fact and dimension tables.

    Args:
        conn: Database connection

    Returns:
        dict: Integrity check results
    """
    cursor = conn.cursor()
    results = {}

    logger.info("\n" + "=" * 70)
    logger.info("VALIDATING REFERENTIAL INTEGRITY")
    logger.info("=" * 70)

    # Check for orphaned customer references
    cursor.execute("""
        SELECT COUNT(*)
        FROM fact_sales f
        LEFT JOIN dim_customers c ON f.CustomerID = c.CustomerID
        WHERE c.CustomerID IS NULL
    """)
    orphaned_customers = cursor.fetchone()[0]
    results["orphaned_customers"] = orphaned_customers

    status = "✅ PASS" if orphaned_customers == 0 else "❌ FAIL"
    logger.info(f"{status} - Orphaned Customer References: {orphaned_customers}")

    # Check for orphaned product references
    cursor.execute("""
        SELECT COUNT(*)
        FROM fact_sales f
        LEFT JOIN dim_products p ON f.ProductID = p.ProductID
        WHERE p.ProductID IS NULL
    """)
    orphaned_products = cursor.fetchone()[0]
    results["orphaned_products"] = orphaned_products

    status = "✅ PASS" if orphaned_products == 0 else "❌ FAIL"
    logger.info(f"{status} - Orphaned Product References: {orphaned_products}")

    # Verify all customers have at least one sale
    cursor.execute("""
        SELECT COUNT(DISTINCT c.CustomerID)
        FROM dim_customers c
        LEFT JOIN fact_sales f ON c.CustomerID = f.CustomerID
        WHERE f.TransactionID IS NULL
    """)
    customers_no_sales = cursor.fetchone()[0]
    results["customers_without_sales"] = customers_no_sales
    logger.info(f"ℹ️  INFO - Customers without sales: {customers_no_sales}")

    # Verify all products have at least one sale
    cursor.execute("""
        SELECT COUNT(DISTINCT p.ProductID)
        FROM dim_products p
        LEFT JOIN fact_sales f ON p.ProductID = f.ProductID
        WHERE f.TransactionID IS NULL
    """)
    products_no_sales = cursor.fetchone()[0]
    results["products_without_sales"] = products_no_sales
    logger.info(f"ℹ️  INFO - Products without sales: {products_no_sales}")

    return results


def validate_data_quality(conn: sqlite3.Connection) -> dict[str, Any]:
    """Validate data quality metrics.

    Args:
        conn: Database connection

    Returns:
        dict: Data quality metrics
    """
    cursor = conn.cursor()
    metrics = {}

    logger.info("\n" + "=" * 70)
    logger.info("VALIDATING DATA QUALITY")
    logger.info("=" * 70)

    # Check for NULL values in critical fields
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN Name IS NULL THEN 1 ELSE 0 END) as null_names,
            SUM(CASE WHEN Region IS NULL THEN 1 ELSE 0 END) as null_regions,
            SUM(CASE WHEN CreditScore IS NULL THEN 1 ELSE 0 END) as null_credit_scores
        FROM dim_customers
    """)
    row = cursor.fetchone()
    metrics["customers"] = {
        "total": row[0],
        "null_names": row[1],
        "null_regions": row[2],
        "null_credit_scores": row[3],
    }

    logger.info("📊 dim_customers Quality:")
    logger.info(f"  • Total Records: {row[0]:,}")
    logger.info(f"  • NULL Names: {row[1]} {'✅' if row[1] == 0 else '⚠️'}")
    logger.info(f"  • NULL Regions: {row[2]} {'✅' if row[2] == 0 else '⚠️'}")
    logger.info(f"  • NULL Credit Scores: {row[3]} (acceptable)")

    # Check for invalid sale amounts
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN SaleAmount < 0 THEN 1 ELSE 0 END) as negative_sales,
            SUM(CASE WHEN SaleAmount = 0 THEN 1 ELSE 0 END) as zero_sales,
            MIN(SaleAmount) as min_sale,
            MAX(SaleAmount) as max_sale,
            AVG(SaleAmount) as avg_sale
        FROM fact_sales
    """)
    row = cursor.fetchone()
    metrics["sales"] = {
        "total": row[0],
        "negative_sales": row[1],
        "zero_sales": row[2],
        "min_sale": row[3],
        "max_sale": row[4],
        "avg_sale": row[5],
    }

    logger.info("\n💰 fact_sales Quality:")
    logger.info(f"  • Total Records: {row[0]:,}")
    logger.info(f"  • Negative Sales: {row[1]} {'✅' if row[1] == 0 else '❌'}")
    logger.info(f"  • Zero Sales: {row[2]} ℹ️")
    logger.info(f"  • Min Sale: ${row[3]:,.2f}")
    logger.info(f"  • Max Sale: ${row[4]:,.2f}")
    logger.info(f"  • Avg Sale: ${row[5]:,.2f}")

    return metrics


# ============================================================================
# Sample Analytical Queries
# ============================================================================


def run_sample_queries(conn: sqlite3.Connection) -> None:
    """Run sample analytical queries to demonstrate data warehouse functionality.

    Args:
        conn: Database connection
    """
    cursor = conn.cursor()

    logger.info("\n" + "=" * 70)
    logger.info("SAMPLE ANALYTICAL QUERIES")
    logger.info("=" * 70)

    # Query 1: Total Sales by Region
    logger.info("\n📊 Query 1: Total Sales by Region")
    logger.info("-" * 70)
    cursor.execute("""
        SELECT
            c.Region,
            COUNT(DISTINCT f.TransactionID) AS TotalTransactions,
            COUNT(DISTINCT f.CustomerID) AS UniqueCustomers,
            SUM(f.SaleAmount) AS TotalSales,
            AVG(f.SaleAmount) AS AvgSaleAmount
        FROM fact_sales f
        JOIN dim_customers c ON f.CustomerID = c.CustomerID
        GROUP BY c.Region
        ORDER BY TotalSales DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    logger.info(
        f"{'Region':<15} {'Transactions':<15} {'Customers':<12} {'Total Sales':<15} {'Avg Sale':<12}"
    )
    logger.info("-" * 70)
    for row in rows:
        logger.info(f"{row[0]:<15} {row[1]:<15,} {row[2]:<12,} ${row[3]:<14,.2f} ${row[4]:<11,.2f}")

    # Query 2: Top 10 Products by Revenue
    logger.info("\n📦 Query 2: Top 10 Products by Revenue")
    logger.info("-" * 70)
    cursor.execute("""
        SELECT
            p.ProductName,
            p.Category,
            COUNT(f.TransactionID) AS SalesCount,
            SUM(f.SaleAmount) AS TotalRevenue,
            AVG(f.SaleAmount) AS AvgSalePrice
        FROM fact_sales f
        JOIN dim_products p ON f.ProductID = p.ProductID
        GROUP BY p.ProductID, p.ProductName, p.Category
        ORDER BY TotalRevenue DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()
    logger.info(f"{'Product':<25} {'Category':<15} {'Sales':<8} {'Revenue':<15} {'Avg Price':<12}")
    logger.info("-" * 70)
    for row in rows:
        logger.info(f"{row[0]:<25} {row[1]:<15} {row[2]:<8,} ${row[3]:<14,.2f} ${row[4]:<11,.2f}")

    # Query 3: Sales by Channel
    logger.info("\n🛒 Query 3: Sales by Order Channel")
    logger.info("-" * 70)
    cursor.execute("""
        SELECT
            OrderChannel,
            COUNT(*) AS TransactionCount,
            SUM(SaleAmount) AS TotalRevenue,
            AVG(SaleAmount) AS AvgSaleAmount,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_sales), 2) AS PercentOfTotal
        FROM fact_sales
        GROUP BY OrderChannel
        ORDER BY TotalRevenue DESC
    """)

    rows = cursor.fetchall()
    logger.info(
        f"{'Channel':<15} {'Transactions':<15} {'Revenue':<15} {'Avg Sale':<12} {'% of Total':<12}"
    )
    logger.info("-" * 70)
    for row in rows:
        logger.info(f"{row[0]:<15} {row[1]:<15,} ${row[2]:<14,.2f} ${row[3]:<11,.2f} {row[4]:<11}%")

    # Query 4: Top Customers by Industry
    logger.info("\n🏢 Query 4: Sales by Customer Industry Type")
    logger.info("-" * 70)
    cursor.execute("""
        SELECT
            c.IndustryType,
            COUNT(DISTINCT c.CustomerID) AS CustomerCount,
            COUNT(f.TransactionID) AS TotalTransactions,
            SUM(f.SaleAmount) AS TotalRevenue,
            AVG(f.SaleAmount) AS AvgSaleAmount
        FROM dim_customers c
        LEFT JOIN fact_sales f ON c.CustomerID = f.CustomerID
        GROUP BY c.IndustryType
        ORDER BY TotalRevenue DESC
    """)

    rows = cursor.fetchall()
    logger.info(
        f"{'Industry':<15} {'Customers':<12} {'Transactions':<15} {'Revenue':<15} {'Avg Sale':<12}"
    )
    logger.info("-" * 70)
    for row in rows:
        logger.info(f"{row[0]:<15} {row[1]:<12,} {row[2]:<15,} ${row[3]:<14,.2f} ${row[4]:<11,.2f}")

    # Query 5: Product Category Performance
    logger.info("\n📈 Query 5: Product Category Performance")
    logger.info("-" * 70)
    cursor.execute("""
        SELECT
            p.Category,
            COUNT(DISTINCT p.ProductID) AS ProductCount,
            COUNT(f.TransactionID) AS SalesCount,
            SUM(f.SaleAmount) AS TotalRevenue,
            AVG(f.SaleAmount) AS AvgSaleAmount,
            AVG(f.CommissionPercent) AS AvgCommission
        FROM dim_products p
        LEFT JOIN fact_sales f ON p.ProductID = f.ProductID
        GROUP BY p.Category
        ORDER BY TotalRevenue DESC
    """)

    rows = cursor.fetchall()
    logger.info(
        f"{'Category':<15} {'Products':<10} {'Sales':<8} {'Revenue':<15} {'Avg Sale':<12} {'Avg Comm%':<10}"
    )
    logger.info("-" * 70)
    for row in rows:
        logger.info(
            f"{row[0]:<15} {row[1]:<10,} {row[2]:<8,} ${row[3]:<14,.2f} ${row[4]:<11,.2f} {row[5]:<9.2f}%"
        )


def generate_summary_statistics(conn: sqlite3.Connection) -> dict[str, Any]:
    """Generate overall summary statistics for the data warehouse.

    Args:
        conn: Database connection

    Returns:
        dict: Summary statistics
    """
    cursor = conn.cursor()
    stats = {}

    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 70)

    # Overall metrics
    cursor.execute("""
        SELECT
            COUNT(DISTINCT CustomerID) as unique_customers,
            COUNT(DISTINCT ProductID) as unique_products,
            COUNT(*) as total_transactions,
            SUM(SaleAmount) as total_revenue,
            AVG(SaleAmount) as avg_transaction,
            MIN(SaleAmount) as min_transaction,
            MAX(SaleAmount) as max_transaction,
            AVG(CommissionPercent) as avg_commission
        FROM fact_sales
    """)

    row = cursor.fetchone()
    stats["unique_customers"] = row[0]
    stats["unique_products"] = row[1]
    stats["total_transactions"] = row[2]
    stats["total_revenue"] = row[3]
    stats["avg_transaction"] = row[4]
    stats["min_transaction"] = row[5]
    stats["max_transaction"] = row[6]
    stats["avg_commission"] = row[7]

    logger.info(f"👥 Unique Customers: {row[0]:,}")
    logger.info(f"📦 Unique Products Sold: {row[1]:,}")
    logger.info(f"💳 Total Transactions: {row[2]:,}")
    logger.info(f"💰 Total Revenue: ${row[3]:,.2f}")
    logger.info(f"📊 Average Transaction: ${row[4]:,.2f}")
    logger.info(f"📉 Min Transaction: ${row[5]:,.2f}")
    logger.info(f"📈 Max Transaction: ${row[6]:,.2f}")
    logger.info(f"💵 Average Commission: {row[7]:.2f}%")

    return stats


# ============================================================================
# Main Validation Pipeline
# ============================================================================


def run_validation() -> dict[str, Any]:
    """Run the complete validation pipeline.

    Returns:
        dict: Validation results
    """
    conn = None
    results = {}

    try:
        logger.info("=" * 70)
        logger.info("DATA WAREHOUSE VALIDATION STARTED")
        logger.info("=" * 70)
        logger.info(f"Database: {DW_DATABASE}\n")

        # Create connection
        conn = create_connection()

        # Run all validation checks
        results["schema"] = validate_table_structure(conn)
        results["record_counts"] = validate_record_counts(conn)
        results["referential_integrity"] = validate_referential_integrity(conn)
        results["data_quality"] = validate_data_quality(conn)

        # Run sample queries
        run_sample_queries(conn)

        # Generate summary statistics
        results["summary"] = generate_summary_statistics(conn)

        logger.info("\n" + "=" * 70)
        logger.success("✅ DATA WAREHOUSE VALIDATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)

        return results

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")


# ============================================================================
# Script Entry Point
# ============================================================================


def main() -> None:
    """Main entry point for the validation script."""
    from analytics_project import utils_logger

    # Initialize logging
    utils_logger.init_logger()

    # Run validation
    run_validation()


if __name__ == "__main__":
    main()
