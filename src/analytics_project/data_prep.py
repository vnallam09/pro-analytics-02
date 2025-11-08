"""Module 2: Data Preparation Script with DataScrubber.

File: src/analytics_project/data_prep.py.

This module reads raw CSV files, cleans them using the DataScrubber class,
and saves the processed data to the prepared directory.
"""

# Imports after the opening docstring

import pathlib

import pandas as pd

from .data_scrubber import DataScrubber
from .utils_logger import init_logger, logger, project_root

# Set up paths as constants
DATA_DIR: pathlib.Path = project_root.joinpath("data")
RAW_DATA_DIR: pathlib.Path = DATA_DIR.joinpath("raw")
PREPARED_DATA_DIR: pathlib.Path = DATA_DIR.joinpath("prepared")


# Define a reusable function that accepts a full path.
def read_and_log(path: pathlib.Path) -> pd.DataFrame:
    """Read a CSV at the given path into a DataFrame, with friendly logging.

    We know reading a csv file can fail
    (the file might not exist, it could be corrupted),
    so we put the statement in a try block.
    It could fail due to a FileNotFoundError or other exceptions.
    If it succeeds, we log the shape of the DataFrame.
    If it fails, we log an error and return an empty DataFrame.
    """
    try:
        # Typically, we log the start of a file read operation
        logger.info(f"Reading raw data from {path}.")
        df = pd.read_csv(path)
        # Typically, we log the successful completion of a file read operation
        logger.info(
            f"{path.name}: loaded DataFrame with shape {df.shape[0]} rows x {df.shape[1]} cols"
        )
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return pd.DataFrame()


# Define a main function to start our data processing pipeline.


def process_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and process customer data.

    Args:
        df: Raw customer DataFrame

    Returns:
        Cleaned customer DataFrame
    """
    logger.info("Processing customer data...")
    scrubber = DataScrubber(df)

    # Check consistency before cleaning
    before_stats = scrubber.check_data_consistency_before_cleaning()
    null_counts = before_stats["null_counts"]
    null_sum = null_counts.sum() if isinstance(null_counts, pd.Series) else null_counts
    logger.info(
        f"Before cleaning - Null counts: {null_sum}, Duplicates: {before_stats['duplicate_count']}"
    )

    # Remove duplicates
    df_cleaned = scrubber.remove_duplicate_records()

    # Handle missing values
    scrubber = DataScrubber(df_cleaned)
    df_cleaned = scrubber.handle_missing_data(fill_value="Unknown")

    # Format Region column to standardize case
    scrubber = DataScrubber(df_cleaned)
    df_cleaned = scrubber.format_column_strings_to_upper_and_trim("Region")

    # Parse JoinDate to standard datetime
    scrubber = DataScrubber(df_cleaned)
    df_cleaned = scrubber.parse_dates_to_add_standard_datetime("JoinDate")

    # Check consistency after cleaning
    scrubber = DataScrubber(df_cleaned)
    after_stats = scrubber.check_data_consistency_after_cleaning()
    null_counts_after = after_stats["null_counts"]
    null_sum_after = (
        null_counts_after.sum() if isinstance(null_counts_after, pd.Series) else null_counts_after
    )
    logger.info(
        f"After cleaning - Null counts: {null_sum_after}, Duplicates: {after_stats['duplicate_count']}"
    )

    logger.info(f"Customer data processed: {len(df_cleaned)} rows")
    return df_cleaned


def process_products(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and process product data.

    Args:
        df: Raw product DataFrame

    Returns:
        Cleaned product DataFrame
    """
    logger.info("Processing product data...")
    scrubber = DataScrubber(df)

    # Check consistency before cleaning
    before_stats = scrubber.check_data_consistency_before_cleaning()
    null_counts = before_stats["null_counts"]
    null_sum = null_counts.sum() if isinstance(null_counts, pd.Series) else null_counts
    logger.info(
        f"Before cleaning - Null counts: {null_sum}, Duplicates: {before_stats['duplicate_count']}"
    )

    # Remove duplicates
    df_cleaned = scrubber.remove_duplicate_records()

    # Handle missing ReorderLevel values
    scrubber = DataScrubber(df_cleaned)
    df_cleaned = scrubber.handle_missing_data(fill_value=0)

    # Check consistency after cleaning
    scrubber = DataScrubber(df_cleaned)
    after_stats = scrubber.check_data_consistency_after_cleaning()
    null_counts_after = after_stats["null_counts"]
    null_sum_after = (
        null_counts_after.sum() if isinstance(null_counts_after, pd.Series) else null_counts_after
    )
    logger.info(
        f"After cleaning - Null counts: {null_sum_after}, Duplicates: {after_stats['duplicate_count']}"
    )

    logger.info(f"Product data processed: {len(df_cleaned)} rows")
    return df_cleaned


def process_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and process sales data.

    Args:
        df: Raw sales DataFrame

    Returns:
        Cleaned sales DataFrame
    """
    logger.info("Processing sales data...")
    scrubber = DataScrubber(df)

    # Check consistency before cleaning
    before_stats = scrubber.check_data_consistency_before_cleaning()
    null_counts = before_stats["null_counts"]
    null_sum = null_counts.sum() if isinstance(null_counts, pd.Series) else null_counts
    logger.info(
        f"Before cleaning - Null counts: {null_sum}, Duplicates: {before_stats['duplicate_count']}"
    )

    # Remove duplicates
    df_cleaned = scrubber.remove_duplicate_records()

    # Drop rows with missing critical data
    scrubber = DataScrubber(df_cleaned)
    df_cleaned = scrubber.handle_missing_data(drop=True)

    # Convert SaleAmount from string to float
    scrubber = DataScrubber(df_cleaned)
    df_cleaned = scrubber.convert_column_to_new_data_type("SaleAmount", float)

    # Remove outliers from SaleAmount using IQR method
    scrubber = DataScrubber(df_cleaned)
    rows_before_outlier_removal = len(df_cleaned)
    df_cleaned = scrubber.filter_column_outliers_iqr("SaleAmount", multiplier=1.5)
    outliers_removed = rows_before_outlier_removal - len(df_cleaned)
    logger.info(f"Removed {outliers_removed} outliers from SaleAmount using IQR method")

    # Note: SaleDate has mixed/invalid formats (e.g., "2023-13-01"), skipping date parsing
    # to avoid errors. Consider data quality improvements at source.

    # Check consistency after cleaning
    scrubber = DataScrubber(df_cleaned)
    after_stats = scrubber.check_data_consistency_after_cleaning()
    null_counts_after = after_stats["null_counts"]
    null_sum_after = (
        null_counts_after.sum() if isinstance(null_counts_after, pd.Series) else null_counts_after
    )
    logger.info(
        f"After cleaning - Null counts: {null_sum_after}, Duplicates: {after_stats['duplicate_count']}"
    )

    logger.info(f"Sales data processed: {len(df_cleaned)} rows")
    return df_cleaned


def save_cleaned_data(df: pd.DataFrame, filename: str) -> None:
    """Save cleaned DataFrame to the prepared directory.

    Args:
        df: Cleaned DataFrame
        filename: Name of the file to save
    """
    output_path = PREPARED_DATA_DIR.joinpath(filename)

    # Ensure the prepared directory exists
    PREPARED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to {output_path}")
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")


def main() -> None:
    """Process raw data using DataScrubber and save to prepared directory."""
    logger.info("=" * 80)
    logger.info("Starting data preparation with DataScrubber...")
    logger.info("=" * 80)

    # Build explicit paths for each file under data/raw
    customer_path = RAW_DATA_DIR.joinpath("customers_data.csv")
    product_path = RAW_DATA_DIR.joinpath("products_data.csv")
    sales_path = RAW_DATA_DIR.joinpath("sales_data.csv")

    # Process customers
    logger.info("-" * 80)
    customers_df = read_and_log(customer_path)
    if not customers_df.empty:
        customers_cleaned = process_customers(customers_df)
        save_cleaned_data(customers_cleaned, "customers_prepared.csv")

    # Process products
    logger.info("-" * 80)
    products_df = read_and_log(product_path)
    if not products_df.empty:
        products_cleaned = process_products(products_df)
        save_cleaned_data(products_cleaned, "products_prepared.csv")

    # Process sales
    logger.info("-" * 80)
    sales_df = read_and_log(sales_path)
    if not sales_df.empty:
        sales_cleaned = process_sales(sales_df)
        save_cleaned_data(sales_cleaned, "sales_prepared.csv")

    logger.info("=" * 80)
    logger.info("Data preparation complete.")
    logger.info("=" * 80)


# Standard Python idiom to run this module as a script when executed directly.

if __name__ == "__main__":
    # Initialize logger
    init_logger()

    # Call the main function by adding () after the function name
    main()
