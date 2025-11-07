"""scripts/data_preparation/prepare_products.py.

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

    # For products, ProductID should be unique - use it to identify duplicates
    # Keep the first occurrence of each ProductID
    if 'productid' in df.columns:
        df = df.drop_duplicates(subset=['productid'], keep='first')
        logger.info("Removed duplicates based on 'productid' column")
    else:
        # Fallback to removing exact duplicate rows if productid column doesn't exist
        df = df.drop_duplicates()
        logger.info("Removed exact duplicate rows (no productid column found)")

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
    # NA means missing or "not a number" - ask your AI for details
    missing_by_col = df.isna().sum()
    logger.info(f"Missing values by column before handling:\n{missing_by_col}")

    # Implement appropriate missing value handling for product data
    # Strategy based on the actual columns in products_data.csv

    # 1. ProductID is required - drop rows without it
    if 'productid' in df.columns:
        df = df.dropna(subset=['productid'])
        logger.info("Dropped rows with missing productid")

    # 2. ProductName - fill with 'Unknown Product' if missing
    if 'productname' in df.columns:
        df['productname'] = df['productname'].fillna('Unknown Product')
        logger.info("Filled missing productname with 'Unknown Product'")

    # 3. Category - fill with the most common category (mode)
    if 'category' in df.columns:
        if df['category'].isna().sum() > 0:
            most_common_category = df['category'].mode()[0]
            df['category'] = df['category'].fillna(most_common_category)
            logger.info(f"Filled missing category with mode: '{most_common_category}'")

    # 4. UnitPrice - fill with median price (less affected by outliers)
    if 'unitprice' in df.columns:
        if df['unitprice'].isna().sum() > 0:
            median_price = df['unitprice'].median()
            df['unitprice'] = df['unitprice'].fillna(median_price)
            logger.info(f"Filled missing unitprice with median: {median_price:.2f}")

    # 5. ReorderLevel - fill with median reorder level
    if 'reorderlevel' in df.columns:
        if df['reorderlevel'].isna().sum() > 0:
            median_reorder = df['reorderlevel'].median()
            df['reorderlevel'] = df['reorderlevel'].fillna(median_reorder)
            logger.info(f"Filled missing reorderlevel with median: {median_reorder}")

    # 6. StorageType - fill with the most common storage type (mode)
    if 'storagetype' in df.columns:
        if df['storagetype'].isna().sum() > 0:
            most_common_storage = df['storagetype'].mode()[0]
            df['storagetype'] = df['storagetype'].fillna(most_common_storage)
            logger.info(f"Filled missing storagetype with mode: '{most_common_storage}'")

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
    # IQR = Q3 - Q1, outliers are values beyond Q1 - 1.5*IQR or Q3 + 1.5*IQR

    numeric_columns = ['unitprice', 'reorderlevel']

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

    # Implement standardization for product data

    # 1. Standardize ProductName - use Title Case for consistency
    if 'productname' in df.columns:
        df['productname'] = df['productname'].str.title().str.strip()
        logger.info("Standardized productname to Title Case")

    # 2. Standardize Category - use Title Case for consistency
    if 'category' in df.columns:
        df['category'] = df['category'].str.title().str.strip()
        logger.info("Standardized category to Title Case")

    # 3. Standardize StorageType - use Title Case for consistency
    if 'storagetype' in df.columns:
        df['storagetype'] = df['storagetype'].str.title().str.strip()
        logger.info("Standardized storagetype to Title Case")

    # 4. Round UnitPrice to 2 decimal places for currency consistency
    if 'unitprice' in df.columns:
        df['unitprice'] = df['unitprice'].round(2)
        logger.info("Rounded unitprice to 2 decimal places")

    # 5. Ensure ReorderLevel is integer (no decimal places needed for counts)
    if 'reorderlevel' in df.columns:
        df['reorderlevel'] = df['reorderlevel'].astype(int)
        logger.info("Converted reorderlevel to integer")

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

    # Implement data validation rules specific to products
    initial_count = len(df)

    # 1. Validate UnitPrice - must be positive
    if 'unitprice' in df.columns:
        invalid_prices = df[df['unitprice'] <= 0].shape[0]
        if invalid_prices > 0:
            logger.warning(f"Found {invalid_prices} products with invalid prices (<= 0)")
            df = df[df['unitprice'] > 0]
            logger.info(f"Removed {invalid_prices} products with invalid prices")

    # 2. Validate ReorderLevel - must be non-negative integer
    if 'reorderlevel' in df.columns:
        invalid_reorder = df[df['reorderlevel'] < 0].shape[0]
        if invalid_reorder > 0:
            logger.warning(f"Found {invalid_reorder} products with negative reorder levels")
            df = df[df['reorderlevel'] >= 0]
            logger.info(f"Removed {invalid_reorder} products with negative reorder levels")

    # 3. Validate Category - must not be empty
    if 'category' in df.columns:
        empty_category = df[df['category'].str.strip() == ''].shape[0]
        if empty_category > 0:
            logger.warning(f"Found {empty_category} products with empty category")
            df = df[df['category'].str.strip() != '']
            logger.info(f"Removed {empty_category} products with empty category")

    # 4. Validate StorageType - must be either 'Warehouse' or 'Retail'
    if 'storagetype' in df.columns:
        valid_storage_types = ['Warehouse', 'Retail']
        invalid_storage = df[~df['storagetype'].isin(valid_storage_types)].shape[0]
        if invalid_storage > 0:
            logger.warning(
                f"Found {invalid_storage} products with invalid storage types "
                f"(not in {valid_storage_types})"
            )
            df = df[df['storagetype'].isin(valid_storage_types)]
            logger.info(f"Removed {invalid_storage} products with invalid storage types")

    # 5. Validate ProductID - must be unique (should already be handled, but double-check)
    if 'productid' in df.columns:
        duplicate_ids = df['productid'].duplicated().sum()
        if duplicate_ids > 0:
            logger.warning(f"Found {duplicate_ids} duplicate product IDs")
            df = df.drop_duplicates(subset=['productid'], keep='first')
            logger.info(f"Removed {duplicate_ids} duplicate product IDs")

    removed_count = initial_count - len(df)
    logger.info(f"Total rows removed during validation: {removed_count}")
    logger.info(f"{len(df)} records remaining after validation")
    logger.info("Data validation complete")
    return df


def main() -> None:
    """Main function for processing product data."""
    logger.info("==================================")
    logger.info("STARTING prepare_products_data.py")
    logger.info("==================================")

    logger.info(f"Root         : {PROJECT_ROOT}")
    logger.info(f"data/raw     : {RAW_DATA_DIR}")
    logger.info(f"data/prepared: {PREPARED_DATA_DIR}")
    logger.info(f"scripts      : {SCRIPTS_DIR}")

    input_file = "products_data.csv"
    output_file = "products_prepared.csv"

    # Read raw data
    df = read_raw_data(input_file)

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
    logger.info("FINISHED prepare_products_data.py")
    logger.info("==================================")


# -------------------
# Conditional Execution Block
# -------------------

if __name__ == "__main__":
    from analytics_project.utils_logger import init_logger

    init_logger()
    main()
