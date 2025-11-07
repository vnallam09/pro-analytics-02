"""scripts/data_preparation/prepare_sales.py.

This script reads data from the data/raw folder, cleans the data,
and writes the cleaned version to the data/prepared folder.

Tasks:
- Remove duplicates
- Handle missing values
- Remove outliers
- Ensure consistent formatting

"""

#####################################
# Import Modules at the Top
#####################################

# Import from Python Standard Library
import pathlib
import sys

# Import from external packages (requires a virtual environment)
import pandas as pd

# Ensure project root is in sys.path for local imports (now 3 parents are needed)
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

# Import local modules (e.g. utils/logger.py)
from analytics_project.utils_logger import logger

# Optional: Use a data_scrubber module for common data cleaning tasks
# from analytics_project.utils_data_scrubber import DataScrubber


# Constants
SCRIPTS_DATA_PREP_DIR: pathlib.Path = (
    pathlib.Path(__file__).resolve().parent
)  # Directory of the current script (data_preparation)
SCRIPTS_DIR: pathlib.Path = SCRIPTS_DATA_PREP_DIR.parent  # analytics_project
SRC_DIR: pathlib.Path = SCRIPTS_DIR.parent  # src
PROJECT_ROOT: pathlib.Path = SRC_DIR.parent  # project root
DATA_DIR: pathlib.Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: pathlib.Path = DATA_DIR / "raw"
PREPARED_DATA_DIR: pathlib.Path = DATA_DIR / "prepared"  # place to store prepared data


# Ensure the directories exist or create them
DATA_DIR.mkdir(exist_ok=True)
RAW_DATA_DIR.mkdir(exist_ok=True)
PREPARED_DATA_DIR.mkdir(exist_ok=True)

#####################################
# Define Functions - Reusable blocks of code / instructions
#####################################


def read_raw_data(file_name: str) -> pd.DataFrame:
    """Read raw data from CSV.

    Args:
        file_name (str): Name of the CSV file to read.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    logger.info(f"FUNCTION START: read_raw_data with file_name={file_name}")
    file_path = RAW_DATA_DIR.joinpath(file_name)
    logger.info(f"Reading data from {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded dataframe with {len(df)} rows and {len(df.columns)} columns")

    # Data profiling to understand the dataset
    logger.info("=" * 50)
    logger.info("DATA PROFILING")
    logger.info("=" * 50)

    # 1. Column names and data types
    logger.info(f"\nColumn names: {', '.join(df.columns.tolist())}")
    logger.info(f"\nColumn datatypes:\n{df.dtypes}")

    # 2. Unique value counts per column
    logger.info(f"\nNumber of unique values per column:\n{df.nunique()}")

    # 3. Missing values summary
    missing_counts = df.isna().sum()
    if missing_counts.sum() > 0:
        logger.info(f"\nMissing values per column:\n{missing_counts[missing_counts > 0]}")
        logger.info(f"Total missing values: {missing_counts.sum()}")
    else:
        logger.info("\nNo missing values found")

    # 4. Basic statistics for numeric columns
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    if numeric_cols:
        logger.info(f"\nNumeric columns: {', '.join(numeric_cols)}")
        logger.info(f"\nBasic statistics for numeric columns:\n{df[numeric_cols].describe()}")

    # 5. Sample of categorical columns
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    if categorical_cols:
        logger.info(f"\nCategorical columns: {', '.join(categorical_cols)}")
        for col in categorical_cols:
            unique_count = df[col].nunique()
            if unique_count <= 10:  # Show value counts for low-cardinality columns
                logger.info(f"\nValue counts for '{col}':\n{df[col].value_counts()}")
            else:
                logger.info(
                    f"\n'{col}' has {unique_count} unique values (top 5):\n{df[col].value_counts().head()}"
                )

    # 6. Duplicate rows
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        logger.info(f"\nFound {duplicate_count} duplicate rows")
    else:
        logger.info("\nNo duplicate rows found")

    logger.info("=" * 50)

    return df


def save_prepared_data(df: pd.DataFrame, file_name: str) -> None:
    """Save cleaned data to CSV.

    Args:
        df (pd.DataFrame): Cleaned DataFrame.
        file_name (str): Name of the output file.
    """
    logger.info(
        f"FUNCTION START: save_prepared_data with file_name={file_name}, dataframe shape={df.shape}"
    )
    file_path = PREPARED_DATA_DIR.joinpath(file_name)
    df.to_csv(file_path, index=False)
    logger.info(f"Data saved to {file_path}")


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows from the DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with duplicates removed.
    """
    logger.info(f"FUNCTION START: remove_duplicates with dataframe shape={df.shape}")
    initial_count = len(df)

    # For sales, TransactionID should be unique - use it to identify duplicates
    # Keep the first occurrence of each TransactionID
    if 'transactionid' in df.columns:
        df = df.drop_duplicates(subset=['transactionid'], keep='first')
        logger.info("Removed duplicates based on 'transactionid' column")
    else:
        # Fallback to removing exact duplicate rows if transactionid column doesn't exist
        df = df.drop_duplicates()
        logger.info("Removed exact duplicate rows (no transactionid column found)")

    removed_count = initial_count - len(df)
    logger.info(f"Removed {removed_count} duplicate rows")
    logger.info(f"{len(df)} records remaining after removing duplicates.")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values by filling or dropping.

    This logic is specific to the actual data and business rules.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with missing values handled.
    """
    logger.info(f"FUNCTION START: handle_missing_values with dataframe shape={df.shape}")

    # Log missing values by column before handling
    missing_by_col = df.isna().sum()
    logger.info(f"Missing values by column before handling:\n{missing_by_col}")

    # Implement appropriate missing value handling for sales data

    # 1. TransactionID is required - drop rows without it
    if 'transactionid' in df.columns:
        df = df.dropna(subset=['transactionid'])
        logger.info("Dropped rows with missing transactionid")

    # 2. CampaignID - fill with 0 (meaning no campaign)
    if 'campaignid' in df.columns:
        if df['campaignid'].isna().sum() > 0:
            df['campaignid'] = df['campaignid'].fillna(0)
            logger.info("Filled missing campaignid with 0 (no campaign)")

    # 3. SaleAmount - handle '?' values and convert to numeric, then fill with 0
    if 'saleamount' in df.columns:
        # Replace '?' with NaN
        df['saleamount'] = df['saleamount'].replace('?', pd.NA)
        # Convert to numeric
        df['saleamount'] = pd.to_numeric(df['saleamount'], errors='coerce')
        # Fill remaining NaN with 0
        if df['saleamount'].isna().sum() > 0:
            df['saleamount'] = df['saleamount'].fillna(0)
            logger.info("Converted saleamount to numeric and filled missing values with 0")

    # 4. CommissionPercent - fill with median commission (typical for the dataset)
    if 'commissionpercent' in df.columns:
        if df['commissionpercent'].isna().sum() > 0:
            median_commission = df['commissionpercent'].median()
            df['commissionpercent'] = df['commissionpercent'].fillna(median_commission)
            logger.info(f"Filled missing commissionpercent with median: {median_commission:.2f}")

    # 5. Required fields - drop rows if missing
    required_fields = ['customerid', 'productid', 'storeid']
    for field in required_fields:
        if field in df.columns:
            initial_len = len(df)
            df = df.dropna(subset=[field])
            dropped = initial_len - len(df)
            if dropped > 0:
                logger.info(f"Dropped {dropped} rows with missing {field}")

    # Log missing values by column after handling
    missing_after = df.isna().sum()
    logger.info(f"Missing values by column after handling:\n{missing_after}")
    logger.info(f"{len(df)} records remaining after handling missing values.")
    return df


def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Remove outliers based on thresholds.

    This logic is very specific to the actual data and business rules.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with outliers removed.
    """
    logger.info(f"FUNCTION START: remove_outliers with dataframe shape={df.shape}")
    initial_count = len(df)

    # Use IQR method to identify and remove outliers in numeric columns
    numeric_columns = ['saleamount', 'commissionpercent']

    for col in numeric_columns:
        if col in df.columns:
            # Check if column is numeric
            if df[col].dtype in ['int64', 'float64']:
                # Calculate quartiles and IQR
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1

                # Calculate bounds
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                # Count outliers before removal
                outliers_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()

                # Remove outliers
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

                logger.info(
                    f"Applied IQR outlier removal to '{col}': "
                    f"bounds [{lower_bound:.2f}, {upper_bound:.2f}], "
                    f"removed {outliers_count} outliers"
                )

    removed_count = initial_count - len(df)
    logger.info(f"Removed {removed_count} total outlier rows")
    logger.info(f"{len(df)} records remaining after removing outliers.")
    return df


def standardize_formats(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize the formatting of various columns.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with standardized formatting.
    """
    logger.info(f"FUNCTION START: standardize_formats with dataframe shape={df.shape}")

    # Create a copy to avoid SettingWithCopyWarning
    df = df.copy()

    # Implement standardization for sales data

    # 1. Standardize OrderChannel - use Title Case for consistency
    if 'orderchannel' in df.columns:
        df['orderchannel'] = df['orderchannel'].str.title().str.strip()
        logger.info("Standardized orderchannel to Title Case")

    # 2. Standardize SaleDate - convert to datetime format, handle errors
    if 'saledate' in df.columns:
        df['saledate'] = pd.to_datetime(df['saledate'], format='%m/%d/%Y', errors='coerce')
        # Drop rows with invalid dates
        invalid_dates = df['saledate'].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Found {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=['saledate'])
            logger.info(f"Removed {invalid_dates} rows with invalid dates")
        logger.info("Converted saledate to datetime format")

    # 3. Round SaleAmount to 2 decimal places for currency consistency
    if 'saleamount' in df.columns:
        df['saleamount'] = df['saleamount'].round(2)
        logger.info("Rounded saleamount to 2 decimal places")

    # 4. Round CommissionPercent to 1 decimal place
    if 'commissionpercent' in df.columns:
        df['commissionpercent'] = df['commissionpercent'].round(1)
        logger.info("Rounded commissionpercent to 1 decimal place")

    # 5. Ensure integer types for ID columns
    id_columns = ['transactionid', 'customerid', 'productid', 'storeid', 'campaignid']
    for col in id_columns:
        if col in df.columns:
            df[col] = df[col].astype(int)
    logger.info("Converted ID columns to integer type")

    logger.info("Completed standardizing formats")
    return df


def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate data against business rules.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Validated DataFrame.
    """
    logger.info(f"FUNCTION START: validate_data with dataframe shape={df.shape}")

    # Implement data validation rules specific to sales
    initial_count = len(df)

    # 1. Validate SaleAmount - must be non-negative
    if 'saleamount' in df.columns:
        invalid_amounts = df[df['saleamount'] < 0].shape[0]
        if invalid_amounts > 0:
            logger.warning(f"Found {invalid_amounts} sales with negative amounts")
            df = df[df['saleamount'] >= 0]
            logger.info(f"Removed {invalid_amounts} sales with negative amounts")

    # 2. Validate CommissionPercent - must be between 0 and 100
    if 'commissionpercent' in df.columns:
        invalid_commission = df[
            (df['commissionpercent'] < 0) | (df['commissionpercent'] > 100)
        ].shape[0]
        if invalid_commission > 0:
            logger.warning(f"Found {invalid_commission} sales with invalid commission percent")
            df = df[(df['commissionpercent'] >= 0) & (df['commissionpercent'] <= 100)]
            logger.info(f"Removed {invalid_commission} sales with invalid commission percent")

    # 3. Validate OrderChannel - must be one of the valid channels
    if 'orderchannel' in df.columns:
        valid_channels = ['Phone', 'Mobile', 'Catalog', 'Online', 'Instore']
        invalid_channels = df[~df['orderchannel'].isin(valid_channels)].shape[0]
        if invalid_channels > 0:
            logger.warning(
                f"Found {invalid_channels} sales with invalid order channels "
                f"(not in {valid_channels})"
            )
            df = df[df['orderchannel'].isin(valid_channels)]
            logger.info(f"Removed {invalid_channels} sales with invalid order channels")

    # 4. Validate TransactionID - must be unique
    if 'transactionid' in df.columns:
        duplicate_ids = df['transactionid'].duplicated().sum()
        if duplicate_ids > 0:
            logger.warning(f"Found {duplicate_ids} duplicate transaction IDs")
            df = df.drop_duplicates(subset=['transactionid'], keep='first')
            logger.info(f"Removed {duplicate_ids} duplicate transaction IDs")

    removed_count = initial_count - len(df)
    logger.info(f"Total rows removed during validation: {removed_count}")
    logger.info(f"{len(df)} records remaining after validation")
    logger.info("Data validation complete")
    return df


#####################################
# Define Main Function - The main entry point of the script
#####################################


def main() -> None:
    """Process sales data through the cleaning pipeline."""
    logger.info("==================================")
    logger.info("STARTING prepare_sales_data.py")
    logger.info("==================================")

    logger.info(f"Root         : {PROJECT_ROOT}")
    logger.info(f"data/raw     : {RAW_DATA_DIR}")
    logger.info(f"data/prepared: {PREPARED_DATA_DIR}")
    logger.info(f"scripts      : {SCRIPTS_DIR}")

    input_file = "sales_data.csv"
    output_file = "sales_prepared.csv"

    # Read raw data
    df = read_raw_data(input_file)

    # Record original shape
    original_shape = df.shape

    # Log initial dataframe information
    logger.info(f"Initial dataframe columns: {', '.join(df.columns.tolist())}")
    logger.info(f"Initial dataframe shape: {df.shape}")

    # Clean column names
    original_columns = df.columns.tolist()
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    # Log if any column names changed
    changed_columns = [
        f"{old} -> {new}" for old, new in zip(original_columns, df.columns) if old != new
    ]
    if changed_columns:
        logger.info(f"Cleaned column names: {', '.join(changed_columns)}")

    # Remove duplicates
    df = remove_duplicates(df)

    # Handle missing values
    df = handle_missing_values(df)

    # Remove outliers
    df = remove_outliers(df)

    # Validate data
    df = validate_data(df)

    # Standardize formats
    df = standardize_formats(df)

    # Save prepared data
    save_prepared_data(df, output_file)

    logger.info("==================================")
    logger.info(f"Original shape: {original_shape}")
    logger.info(f"Cleaned shape:  {df.shape}")
    logger.info("==================================")
    logger.info("FINISHED prepare_sales_data.py")
    logger.info("==================================")


#####################################
# Conditional Execution Block
# Ensures the script runs only when executed directly
# This is a common Python convention.
#####################################

if __name__ == "__main__":
    from analytics_project.utils_logger import init_logger

    init_logger()
    main()
