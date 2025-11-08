"""Unit tests for the DataScrubber class.

This module contains comprehensive tests for all DataScrubber methods
to verify they have been correctly defined and perform the necessary logic correctly.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add the src directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analytics_project.data_scrubber import DataScrubber


class TestDataScrubberInit(unittest.TestCase):
    """Test DataScrubber initialization."""

    def test_init_with_dataframe(self):
        """Test that DataScrubber initializes correctly with a DataFrame."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        scrubber = DataScrubber(df)
        self.assertIsInstance(scrubber.df, pd.DataFrame)
        pd.testing.assert_frame_equal(scrubber.df, df)


class TestDataConsistencyChecks(unittest.TestCase):
    """Test data consistency checking methods."""

    def test_check_data_consistency_before_cleaning(self):
        """Test checking data consistency before cleaning."""
        df = pd.DataFrame({
            "A": [1, 2, None, 4, 4],
            "B": [5, None, 7, 8, 8],
            "C": [9, 10, 11, 12, 12]
        })
        scrubber = DataScrubber(df)
        result = scrubber.check_data_consistency_before_cleaning()

        self.assertIn("null_counts", result)
        self.assertIn("duplicate_count", result)

        # Type assertion for linter
        null_counts = result["null_counts"]
        assert isinstance(null_counts, pd.Series)

        self.assertEqual(null_counts["A"], 1)
        self.assertEqual(null_counts["B"], 1)
        self.assertEqual(result["duplicate_count"], 1)

    def test_check_data_consistency_after_cleaning(self):
        """Test checking data consistency after cleaning (no nulls/duplicates)."""
        df = pd.DataFrame({
            "A": [1, 2, 3, 4],
            "B": [5, 6, 7, 8],
            "C": [9, 10, 11, 12]
        })
        scrubber = DataScrubber(df)
        result = scrubber.check_data_consistency_after_cleaning()

        # Type assertion for linter
        null_counts = result["null_counts"]
        assert isinstance(null_counts, pd.Series)

        self.assertEqual(null_counts.sum(), 0)
        self.assertEqual(result["duplicate_count"], 0)

    def test_check_data_consistency_after_cleaning_with_nulls_fails(self):
        """Test that checking consistency after cleaning fails with nulls."""
        df = pd.DataFrame({"A": [1, 2, None], "B": [4, 5, 6]})
        scrubber = DataScrubber(df)

        with self.assertRaises(AssertionError) as context:
            scrubber.check_data_consistency_after_cleaning()
        self.assertIn("null values", str(context.exception))

    def test_check_data_consistency_after_cleaning_with_duplicates_fails(self):
        """Test that checking consistency after cleaning fails with duplicates."""
        df = pd.DataFrame({"A": [1, 2, 2], "B": [4, 5, 5]})
        scrubber = DataScrubber(df)

        with self.assertRaises(AssertionError) as context:
            scrubber.check_data_consistency_after_cleaning()
        self.assertIn("duplicate records", str(context.exception))


class TestConvertColumnDataType(unittest.TestCase):
    """Test column data type conversion."""

    def test_convert_column_to_int(self):
        """Test converting a column to integer type."""
        df = pd.DataFrame({"A": ["1", "2", "3"], "B": [4.5, 5.5, 6.5]})
        scrubber = DataScrubber(df)
        result_df = scrubber.convert_column_to_new_data_type("A", int)

        self.assertEqual(result_df["A"].dtype, np.int64)
        self.assertEqual(list(result_df["A"]), [1, 2, 3])

    def test_convert_column_to_float(self):
        """Test converting a column to float type."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": ["4.5", "5.5", "6.5"]})
        scrubber = DataScrubber(df)
        result_df = scrubber.convert_column_to_new_data_type("B", float)

        self.assertEqual(result_df["B"].dtype, np.float64)
        self.assertEqual(list(result_df["B"]), [4.5, 5.5, 6.5])

    def test_convert_column_to_str(self):
        """Test converting a column to string type."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4.5, 5.5, 6.5]})
        scrubber = DataScrubber(df)
        result_df = scrubber.convert_column_to_new_data_type("A", str)

        self.assertEqual(result_df["A"].dtype, object)
        self.assertEqual(list(result_df["A"]), ["1", "2", "3"])

    def test_convert_column_invalid_column_raises_error(self):
        """Test that converting a non-existent column raises ValueError."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.convert_column_to_new_data_type("NonExistent", int)
        self.assertIn("not found", str(context.exception))


class TestDropColumns(unittest.TestCase):
    """Test dropping columns."""

    def test_drop_single_column(self):
        """Test dropping a single column."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
        scrubber = DataScrubber(df)
        result_df = scrubber.drop_columns(["B"])

        self.assertEqual(list(result_df.columns), ["A", "C"])
        self.assertEqual(len(result_df.columns), 2)

    def test_drop_multiple_columns(self):
        """Test dropping multiple columns."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9], "D": [10, 11, 12]})
        scrubber = DataScrubber(df)
        result_df = scrubber.drop_columns(["B", "D"])

        self.assertEqual(list(result_df.columns), ["A", "C"])
        self.assertEqual(len(result_df.columns), 2)

    def test_drop_column_invalid_column_raises_error(self):
        """Test that dropping a non-existent column raises ValueError."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.drop_columns(["NonExistent"])
        self.assertIn("not found", str(context.exception))


class TestFilterColumnOutliers(unittest.TestCase):
    """Test filtering outliers."""

    def test_filter_outliers_numeric_column(self):
        """Test filtering outliers from a numeric column."""
        df = pd.DataFrame({"A": [1, 2, 3, 100, 200], "B": [5, 6, 7, 8, 9]})
        scrubber = DataScrubber(df)
        result_df = scrubber.filter_column_outliers("A", 1, 10)

        self.assertEqual(len(result_df), 3)
        self.assertEqual(list(result_df["A"]), [1, 2, 3])

    def test_filter_outliers_with_bounds(self):
        """Test filtering outliers with specific bounds."""
        df = pd.DataFrame({"Price": [10.5, 20.0, 15.5, 100.0, 5.0, 25.0]})
        scrubber = DataScrubber(df)
        result_df = scrubber.filter_column_outliers("Price", 10.0, 30.0)

        self.assertEqual(len(result_df), 4)
        self.assertTrue(all(result_df["Price"] >= 10.0))
        self.assertTrue(all(result_df["Price"] <= 30.0))

    def test_filter_outliers_invalid_column_raises_error(self):
        """Test that filtering outliers on non-existent column raises ValueError."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.filter_column_outliers("NonExistent", 0, 10)
        self.assertIn("not found", str(context.exception))

    def test_filter_outliers_iqr_removes_outliers(self):
        """Test IQR method removes outliers correctly."""
        # Create data with clear outliers: [1,2,3,4,5,100]
        # Q1=2, Q3=5, IQR=3, lower=2-4.5=-2.5, upper=5+4.5=9.5
        # So 100 should be removed
        df = pd.DataFrame({"Values": [1, 2, 3, 4, 5, 100]})
        scrubber = DataScrubber(df)
        result_df = scrubber.filter_column_outliers_iqr("Values", multiplier=1.5)

        self.assertEqual(len(result_df), 5)
        self.assertEqual(list(result_df["Values"]), [1, 2, 3, 4, 5])
        self.assertNotIn(100, list(result_df["Values"]))

    def test_filter_outliers_iqr_with_custom_multiplier(self):
        """Test IQR method with custom multiplier."""
        df = pd.DataFrame({"Data": [10, 15, 20, 25, 30, 100]})
        scrubber = DataScrubber(df)
        # Using multiplier=1.0 will be stricter than 1.5
        result_df = scrubber.filter_column_outliers_iqr("Data", multiplier=1.0)

        # Should remove the extreme outlier
        self.assertLess(len(result_df), len(df))
        self.assertNotIn(100, list(result_df["Data"]))

    def test_filter_outliers_iqr_no_outliers(self):
        """Test IQR method when there are no outliers."""
        df = pd.DataFrame({"Normal": [10, 12, 14, 16, 18, 20]})
        scrubber = DataScrubber(df)
        result_df = scrubber.filter_column_outliers_iqr("Normal", multiplier=1.5)

        # All values should remain
        self.assertEqual(len(result_df), len(df))

    def test_filter_outliers_iqr_invalid_column_raises_error(self):
        """Test that IQR filtering on non-existent column raises ValueError."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.filter_column_outliers_iqr("NonExistent")
        self.assertIn("not found", str(context.exception))


class TestFormatColumnStrings(unittest.TestCase):
    """Test string formatting methods."""

    def test_format_strings_to_lower_and_trim(self):
        """Test converting strings to lowercase and trimming whitespace."""
        df = pd.DataFrame({"Name": ["  JOHN  ", "JANE", "  BOB"]})
        scrubber = DataScrubber(df)
        result_df = scrubber.format_column_strings_to_lower_and_trim("Name")

        self.assertEqual(list(result_df["Name"]), ["john", "jane", "bob"])

    def test_format_strings_to_upper_and_trim(self):
        """Test converting strings to uppercase and trimming whitespace."""
        df = pd.DataFrame({"Name": ["  john  ", "jane", "  bob"]})
        scrubber = DataScrubber(df)
        result_df = scrubber.format_column_strings_to_upper_and_trim("Name")

        self.assertEqual(list(result_df["Name"]), ["JOHN", "JANE", "BOB"])

    def test_format_strings_mixed_case(self):
        """Test formatting strings with mixed case."""
        df = pd.DataFrame({"City": [" New York ", "LOS ANGELES", "chicago "]})
        scrubber = DataScrubber(df)
        result_df = scrubber.format_column_strings_to_lower_and_trim("City")

        self.assertEqual(list(result_df["City"]), ["new york", "los angeles", "chicago"])

    def test_format_strings_lower_invalid_column_raises_error(self):
        """Test that formatting non-existent column raises ValueError."""
        df = pd.DataFrame({"A": ["test"]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.format_column_strings_to_lower_and_trim("NonExistent")
        self.assertIn("not found", str(context.exception))

    def test_format_strings_upper_invalid_column_raises_error(self):
        """Test that formatting non-existent column raises ValueError."""
        df = pd.DataFrame({"A": ["test"]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.format_column_strings_to_upper_and_trim("NonExistent")
        self.assertIn("not found", str(context.exception))


class TestHandleMissingData(unittest.TestCase):
    """Test missing data handling methods."""

    def test_handle_missing_data_with_drop(self):
        """Test handling missing data by dropping rows."""
        df = pd.DataFrame({"A": [1, 2, None, 4], "B": [5, None, 7, 8]})
        scrubber = DataScrubber(df)
        result_df = scrubber.handle_missing_data(drop=True)

        self.assertEqual(len(result_df), 2)
        self.assertFalse(result_df.isnull().any().any())

    def test_handle_missing_data_with_fill_value(self):
        """Test handling missing data by filling with a value."""
        df = pd.DataFrame({"A": [1, 2, None, 4], "B": [5, None, 7, 8]})
        scrubber = DataScrubber(df)
        result_df = scrubber.handle_missing_data(fill_value=0)

        self.assertFalse(result_df.isnull().any().any())
        self.assertEqual(result_df.loc[2, "A"], 0)
        self.assertEqual(result_df.loc[1, "B"], 0)

    def test_handle_missing_data_with_string_fill(self):
        """Test handling missing data by filling with a string."""
        df = pd.DataFrame({"Name": ["John", None, "Jane"], "Age": [25, 30, None]})
        scrubber = DataScrubber(df)
        result_df = scrubber.handle_missing_data(fill_value="Unknown")

        self.assertFalse(result_df.isnull().any().any())
        self.assertEqual(result_df.loc[1, "Name"], "Unknown")

    def test_handle_missing_data_no_action(self):
        """Test that missing data remains unchanged without action."""
        df = pd.DataFrame({"A": [1, None, 3]})
        scrubber = DataScrubber(df)
        result_df = scrubber.handle_missing_data()

        self.assertTrue(result_df.isnull().any().any())


class TestInspectData(unittest.TestCase):
    """Test data inspection methods."""

    def test_inspect_data_returns_tuple(self):
        """Test that inspect_data returns a tuple of strings."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4.5, 5.5, 6.5]})
        scrubber = DataScrubber(df)
        info_str, describe_str = scrubber.inspect_data()

        self.assertIsInstance(info_str, str)
        self.assertIsInstance(describe_str, str)

    def test_inspect_data_info_contains_column_info(self):
        """Test that info string contains column information."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4.5, 5.5, 6.5]})
        scrubber = DataScrubber(df)
        info_str, _ = scrubber.inspect_data()

        self.assertIn("A", info_str)
        self.assertIn("B", info_str)

    def test_inspect_data_describe_contains_statistics(self):
        """Test that describe string contains statistical information."""
        df = pd.DataFrame({"A": [1, 2, 3, 4, 5]})
        scrubber = DataScrubber(df)
        _, describe_str = scrubber.inspect_data()

        self.assertIn("count", describe_str)
        self.assertIn("mean", describe_str)
        self.assertIn("std", describe_str)


class TestParseDates(unittest.TestCase):
    """Test date parsing methods."""

    def test_parse_dates_from_string_column(self):
        """Test parsing dates from string column."""
        df = pd.DataFrame({
            "DateStr": ["2024-01-01", "2024-02-15", "2024-03-30"],
            "Value": [100, 200, 300]
        })
        scrubber = DataScrubber(df)
        result_df = scrubber.parse_dates_to_add_standard_datetime("DateStr")

        self.assertIn("StandardDateTime", result_df.columns)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result_df["StandardDateTime"]))

    def test_parse_dates_creates_correct_datetime(self):
        """Test that parsed dates are correct."""
        df = pd.DataFrame({"DateStr": ["2024-01-01", "2024-12-31"]})
        scrubber = DataScrubber(df)
        result_df = scrubber.parse_dates_to_add_standard_datetime("DateStr")

        self.assertEqual(result_df["StandardDateTime"][0], pd.Timestamp("2024-01-01"))
        self.assertEqual(result_df["StandardDateTime"][1], pd.Timestamp("2024-12-31"))

    def test_parse_dates_invalid_column_raises_error(self):
        """Test that parsing dates on non-existent column raises ValueError."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.parse_dates_to_add_standard_datetime("NonExistent")
        self.assertIn("not found", str(context.exception))


class TestRemoveDuplicateRecords(unittest.TestCase):
    """Test duplicate removal methods."""

    def test_remove_duplicate_records(self):
        """Test removing duplicate records."""
        df = pd.DataFrame({
            "A": [1, 2, 2, 3, 3, 3],
            "B": [4, 5, 5, 6, 6, 6]
        })
        scrubber = DataScrubber(df)
        result_df = scrubber.remove_duplicate_records()

        self.assertEqual(len(result_df), 3)
        self.assertEqual(result_df.duplicated().sum(), 0)

    def test_remove_duplicates_preserves_first_occurrence(self):
        """Test that duplicate removal preserves first occurrence."""
        df = pd.DataFrame({
            "ID": [1, 2, 2, 3],
            "Name": ["A", "B", "B", "C"]
        })
        scrubber = DataScrubber(df)
        result_df = scrubber.remove_duplicate_records()

        self.assertEqual(len(result_df), 3)
        self.assertEqual(list(result_df["ID"]), [1, 2, 3])

    def test_remove_duplicates_no_duplicates(self):
        """Test removing duplicates when there are none."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        scrubber = DataScrubber(df)
        result_df = scrubber.remove_duplicate_records()

        self.assertEqual(len(result_df), 3)


class TestRenameColumns(unittest.TestCase):
    """Test column renaming methods."""

    def test_rename_single_column(self):
        """Test renaming a single column."""
        df = pd.DataFrame({"OldName": [1, 2, 3], "B": [4, 5, 6]})
        scrubber = DataScrubber(df)
        result_df = scrubber.rename_columns({"OldName": "NewName"})

        self.assertIn("NewName", result_df.columns)
        self.assertNotIn("OldName", result_df.columns)

    def test_rename_multiple_columns(self):
        """Test renaming multiple columns."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
        scrubber = DataScrubber(df)
        result_df = scrubber.rename_columns({"A": "Alpha", "B": "Beta"})

        self.assertEqual(list(result_df.columns), ["Alpha", "Beta", "C"])

    def test_rename_columns_invalid_column_raises_error(self):
        """Test that renaming non-existent column raises ValueError."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.rename_columns({"NonExistent": "NewName"})
        self.assertIn("not found", str(context.exception))


class TestReorderColumns(unittest.TestCase):
    """Test column reordering methods."""

    def test_reorder_columns(self):
        """Test reordering columns."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
        scrubber = DataScrubber(df)
        result_df = scrubber.reorder_columns(["C", "A", "B"])

        self.assertEqual(list(result_df.columns), ["C", "A", "B"])

    def test_reorder_columns_subset(self):
        """Test reordering with subset of columns."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
        scrubber = DataScrubber(df)
        result_df = scrubber.reorder_columns(["B", "A"])

        self.assertEqual(list(result_df.columns), ["B", "A"])
        self.assertNotIn("C", result_df.columns)

    def test_reorder_columns_invalid_column_raises_error(self):
        """Test that reordering with non-existent column raises ValueError."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.reorder_columns(["A", "NonExistent"])
        self.assertIn("not found", str(context.exception))


class TestMethodChaining(unittest.TestCase):
    """Test that methods return DataFrames that can be used in subsequent operations."""

    def test_chain_remove_duplicates_and_handle_missing(self):
        """Test sequential operations on remove_duplicates and handle_missing_data."""
        df = pd.DataFrame({
            "A": [1, 2, 2, None, 4],
            "B": [5, 6, 6, 7, None]
        })
        scrubber = DataScrubber(df)

        # First operation
        result_df = scrubber.remove_duplicate_records()
        self.assertEqual(len(result_df), 4)  # One duplicate removed

        # Second operation on the result
        scrubber2 = DataScrubber(result_df)
        final_df = scrubber2.handle_missing_data(drop=True)

        self.assertEqual(len(final_df), 2)  # Rows with nulls removed
        self.assertFalse(final_df.duplicated().any())
        self.assertFalse(final_df.isnull().any().any())

    def test_chain_format_and_rename(self):
        """Test sequential operations on format and rename."""
        df = pd.DataFrame({"old_name": ["  JOHN  ", "JANE", "  BOB"]})
        scrubber = DataScrubber(df)

        # First operation
        result_df = scrubber.format_column_strings_to_lower_and_trim("old_name")
        self.assertEqual(list(result_df["old_name"]), ["john", "jane", "bob"])

        # Second operation on the result
        scrubber2 = DataScrubber(result_df)
        final_df = scrubber2.rename_columns({"old_name": "name"})

        self.assertIn("name", final_df.columns)
        self.assertEqual(list(final_df["name"]), ["john", "jane", "bob"])

    def test_chain_multiple_operations(self):
        """Test multiple sequential operations."""
        df = pd.DataFrame({
            "A": [1, 2, 2, 3],
            "B": ["  X  ", "Y", "Y", "  Z"],
            "C": [10, 20, 20, 30]
        })
        scrubber = DataScrubber(df)

        # Operation 1: Remove duplicates
        result1 = scrubber.remove_duplicate_records()
        self.assertEqual(len(result1), 3)

        # Operation 2: Format strings
        scrubber2 = DataScrubber(result1)
        result2 = scrubber2.format_column_strings_to_lower_and_trim("B")
        self.assertEqual(list(result2["B"]), ["x", "y", "z"])

        # Operation 3: Rename columns
        scrubber3 = DataScrubber(result2)
        result3 = scrubber3.rename_columns({"A": "ID", "B": "Category"})
        self.assertEqual(list(result3.columns), ["ID", "Category", "C"])

        # Operation 4: Reorder columns
        scrubber4 = DataScrubber(result3)
        final_df = scrubber4.reorder_columns(["ID", "Category", "C"])

        self.assertEqual(len(final_df), 3)
        self.assertEqual(list(final_df.columns), ["ID", "Category", "C"])
        self.assertEqual(list(final_df["Category"]), ["x", "y", "z"])


class TestExceptionHandling(unittest.TestCase):
    """Test that proper exceptions are raised with correct chaining."""

    def test_exception_chaining_convert_column(self):
        """Test that exceptions are properly chained in convert_column_to_new_data_type."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.convert_column_to_new_data_type("NonExistent", int)

        self.assertIsNotNone(context.exception.__cause__)

    def test_exception_chaining_filter_outliers(self):
        """Test that exceptions are properly chained in filter_column_outliers."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.filter_column_outliers("NonExistent", 0, 10)

        self.assertIsNotNone(context.exception.__cause__)

    def test_exception_chaining_format_lower(self):
        """Test that exceptions are properly chained in format_column_strings_to_lower_and_trim."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.format_column_strings_to_lower_and_trim("NonExistent")

        self.assertIsNotNone(context.exception.__cause__)

    def test_exception_chaining_parse_dates(self):
        """Test that exceptions are properly chained in parse_dates_to_add_standard_datetime."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        scrubber = DataScrubber(df)

        with self.assertRaises(ValueError) as context:
            scrubber.parse_dates_to_add_standard_datetime("NonExistent")

        self.assertIsNotNone(context.exception.__cause__)


if __name__ == "__main__":
    unittest.main()
