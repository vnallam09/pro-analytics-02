## P2 Notes (Data Processing with DataScrubber)

### Data Preparation Pipeline (`data_prep.py`)
- **Purpose**: Reads raw CSV files, cleans them using the DataScrubber class, and saves processed data to the prepared directory
- **Input**: Raw CSV files from `data/raw/` (customers, products, sales)
- **Output**: Cleaned CSV files in `data/prepared/`
- **Features**:
  - Removes duplicate records
  - Handles missing values (fill or drop strategies)
  - Standardizes string formatting (uppercase/lowercase, trim whitespace)
  - Converts data types (e.g., string to float)
  - Removes statistical outliers using IQR method
  - Parses date columns to standard datetime format
  - Validates data consistency before and after cleaning
  - Comprehensive logging throughout the process

### DataScrubber Class (`data_scrubber.py`)
A reusable utility class for performing common data cleaning and preparation tasks on pandas DataFrames.

**Available Methods (15 total):**
1. `__init__(df)` - Initialize with a DataFrame
2. `check_data_consistency_before_cleaning()` - Log nulls and duplicates before processing
3. `check_data_consistency_after_cleaning()` - Validate no nulls/duplicates remain
4. `convert_column_to_new_data_type(column, new_type)` - Convert column data types
5. `drop_columns(columns)` - Remove specified columns
6. `filter_column_outliers(column, lower_bound, upper_bound)` - Remove outliers with manual bounds
7. `filter_column_outliers_iqr(column, multiplier=1.5)` - Remove outliers using IQR method
8. `format_column_strings_to_lower_and_trim(column)` - Lowercase and trim strings
9. `format_column_strings_to_upper_and_trim(column)` - Uppercase and trim strings
10. `handle_missing_data(drop=False, fill_value=None)` - Handle missing values
11. `inspect_data()` - Get DataFrame info and statistics
12. `parse_dates_to_add_standard_datetime(column)` - Parse dates to datetime format
13. `remove_duplicate_records()` - Remove duplicate rows
14. `rename_columns(column_mapping)` - Rename columns using dictionary
15. `reorder_columns(columns)` - Reorder DataFrame columns

**Example Usage:**
```python
from analytics_project.data_scrubber import DataScrubber

# Initialize with DataFrame
scrubber = DataScrubber(df)

# Check consistency
before_stats = scrubber.check_data_consistency_before_cleaning()

# Clean the data
df_cleaned = scrubber.remove_duplicate_records()
scrubber = DataScrubber(df_cleaned)
df_cleaned = scrubber.handle_missing_data(fill_value="Unknown")

# Remove outliers using IQR method
scrubber = DataScrubber(df_cleaned)
df_cleaned = scrubber.filter_column_outliers_iqr("SaleAmount", multiplier=1.5)

# Validate results
scrubber = DataScrubber(df_cleaned)
after_stats = scrubber.check_data_consistency_after_cleaning()
```

### Testing & Code Coverage

**Run Unit Tests:**
```shell
# Run all tests
uv run pytest tests/test_data_scrubber.py -v

# Run specific test class
uv run pytest tests/test_data_scrubber.py::TestFilterColumnOutliers -v

# Run with coverage report
uv run pytest tests/test_data_scrubber.py -v --cov=src/analytics_project/data_scrubber --cov-report=term-missing
```

**Test Statistics:**
- Total Tests: 50 (all passing)
- Code Coverage: 100% on data_scrubber.py
- Test Classes: 14 (covering all DataScrubber methods)

**Generate HTML Coverage Report:**
```shell
uv run pytest tests/test_data_scrubber.py --cov=src/analytics_project/data_scrubber --cov-report=html
# Open htmlcov/index.html in browser to view detailed coverage
```

### Run Data Processing Pipeline

```shell
# Process all CSV files (customers, products, sales)
uv run python -m analytics_project.data_prep
```

**Processing Results:**
- **Customers**: 201 → 200 rows (removed 1 duplicate, filled 1 null, standardized Region to uppercase, parsed JoinDate)
- **Products**: 100 rows (filled 1 null in ReorderLevel)
- **Sales**: 2001 → 1933 rows (dropped 2 rows with nulls, removed 66 outliers from SaleAmount using IQR)

**Output Location:** `data/prepared/` directory contains cleaned CSV files

### Commands Used:
```shell
# Run data preparation
uv run python -m analytics_project.data_prep

# Run ETL to create and populate data warehouse
uv run python -m analytics_project.dw.etl_to_dw

# Validate data warehouse
uv run python -m analytics_project.dw.validate_dw

# Git commands
git add -A && git commit -m "Add data processing and warehouse implementation" && git push origin main
```

---

## Data Warehouse Design & Implementation

### Overview
This project implements a **Star Schema** data warehouse optimized for analytics and business intelligence. The design follows dimensional modeling best practices with a central fact table surrounded by dimension tables.

### Schema Design
- **Fact Table**: `fact_sales` (1,931 transactions)
  - Measures: `SaleAmount`, `CommissionPercent`
  - Foreign Keys: `CustomerID`, `ProductID`
  - Attributes: `SaleDate`, `StoreID`, `CampaignID`, `OrderChannel`

- **Dimension Tables**:
  - `dim_customers` (200 records) - Customer demographics and attributes
  - `dim_products` (100 records) - Product catalog and specifications

### Key Features
- ✅ **Referential Integrity**: Foreign key constraints enforced
- ✅ **Performance Optimization**: 8 strategic indexes on fact and dimension tables
- ✅ **Data Quality**: 100% referential integrity validation passed
- ✅ **Total Revenue**: $1,750,640.79 across all transactions

### ETL Pipeline
Create and populate the data warehouse using the ETL script:

```shell
# Run ETL to create schema and load data
uv run python -m analytics_project.dw.etl_to_dw
```

**ETL Process:**
1. Creates data warehouse schema (tables, foreign keys, indexes)
2. Loads dimension tables first (customers, products)
3. Loads fact table with referential integrity checks
4. Validates data quality and relationships

### Validation & Testing
Verify the data warehouse structure and data integrity:

```shell
# Run comprehensive validation
uv run python -m analytics_project.dw.validate_dw
```

**Validation Checks:**
- Table structure and schema verification
- Record counts and data quality metrics
- Referential integrity (0 orphaned records)
- Sample analytical queries demonstrating star schema functionality

### Viewing the Database
The SQLite database can be viewed in VS Code:
1. Locate `data_warehouse.db` in the project root
2. Right-click and select "Open Database" (requires SQLite Viewer extension)
3. Browse tables, run queries, and explore the data

### Documentation
For complete details about the data warehouse design, see:
- **📄 [Data Warehouse Schema Design](./data_warehouse_schema.md)** - Complete schema documentation with DDL, relationships, and query patterns
- **📊 [Validation Results](./DW_VALIDATION_RESULTS.md)** - Validation results, sample queries, and analytical insights

### Sample Insights
- **Top Region**: EAST leads with $600,926 in sales (652 transactions)
- **Best Product Category**: Electronics has highest avg sale ($1,078.88)
- **Channel Distribution**: All order channels evenly balanced (~20% each)
- **Customer Segments**: Retail industry generates most revenue ($360,445)

---

# Pro Analytics 02 Python Starter Repository

> Use this repo to start a professional Python project.

- Additional information: https://github.com/vnallam09/pro-analytics-02
- Project organization: [STRUCTURE](./STRUCTURE.md)
- Build professional skills:
  - **Environment Management**: Every project in isolation
  - **Code Quality**: Automated checks for fewer bugs
  - **Documentation**: Use modern project documentation tools
  - **Testing**: Prove your code works
  - **Version Control**: Collaborate professionally

---

## WORKFLOW 1. Set Up Your Machine

Proper setup is critical.
Complete each step in the following guide and verify carefully.

- [SET UP MACHINE](./SET_UP_MACHINE.md)

---

## WORKFLOW 2. Set Up Your Project

After verifying your machine is set up, set up a new Python project by copying this template.
Complete each step in the following guide.

- [SET UP PROJECT](./SET_UP_PROJECT.md)

It includes the critical commands to set up your local environment (and activate it):

```shell
uv venv
uv python pin 3.12
uv sync --extra dev --extra docs --upgrade
uv run pre-commit install
uv run python --version
```

**Windows (PowerShell):**

```shell
.\.venv\Scripts\activate
```

**macOS / Linux / WSL:**

```shell
source .venv/bin/activate
```

---

## WORKFLOW 3. Daily Workflow

Please ensure that the prior steps have been verified before continuing.
When working on a project, we open just that project in VS Code.

### 3.1 Git Pull from GitHub

Always start with `git pull` to check for any changes made to the GitHub repo.

```shell
git pull
```

### 3.2 Run Checks as You Work

This mirrors real work where we typically:

1. Update dependencies (for security and compatibility).
2. Clean unused cached packages to free space.
3. Use `git add .` to stage all changes.
4. Run ruff and fix minor issues.
5. Update pre-commit periodically.
6. Run pre-commit quality checks on all code files (**twice if needed**, the first pass may fix things).
7. Run tests.

In VS Code, open your repository, then open a terminal (Terminal / New Terminal) and run the following commands one at a time to check the code.

```shell
uv sync --extra dev --extra docs --upgrade
uv cache clean
git add .
uvx ruff check --fix
uvx pre-commit autoupdate
uv run pre-commit run --all-files
git add .
uv run pytest
```

NOTE: The second `git add .` ensures any automatic fixes made by Ruff or pre-commit are included before testing or committing.

<details>
<summary>Click to see a note on best practices</summary>

`uvx` runs the latest version of a tool in an isolated cache, outside the virtual environment.
This keeps the project light and simple, but behavior can change when the tool updates.
For fully reproducible results, or when you need to use the local `.venv`, use `uv run` instead.

</details>

### 3.3 Build Project Documentation

Make sure you have current doc dependencies, then build your docs, fix any errors, and serve them locally to test.

```shell
uv run mkdocs build --strict
uv run mkdocs serve
```

- After running the serve command, the local URL of the docs will be provided. To open the site, press **CTRL and click** the provided link (at the same time) to view the documentation. On a Mac, use **CMD and click**.
- Press **CTRL c** (at the same time) to stop the hosting process.

### 3.4 Execute

This project includes demo code and data warehouse ETL pipelines.
Run the demo Python modules to confirm everything is working.

In VS Code terminal, run:

```shell
# Demo modules
uv run python -m analytics_project.demo_module_basics
uv run python -m analytics_project.demo_module_languages
uv run python -m analytics_project.demo_module_stats
uv run python -m analytics_project.demo_module_viz

# Data processing and warehouse
uv run python -m analytics_project.data_prep          # Clean and prepare data
uv run python -m analytics_project.dw.etl_to_dw       # Create and populate data warehouse
uv run python -m analytics_project.dw.validate_dw     # Validate data warehouse
```

You should see:

- Log messages in the terminal
- Greetings in several languages
- Simple statistics
- A chart window open (close the chart window to continue).

If this works, your project is ready! If not, check:

- Are you in the right folder? (All terminal commands are to be run from the root project folder.)
- Did you run the full `uv sync --extra dev --extra docs --upgrade` command?
- Are there any error messages? (ask for help with the exact error)

---

### 3.5 Git add-commit-push to GitHub

Anytime we make working changes to code is a good time to git add-commit-push to GitHub.

1. Stage your changes with git add.
2. Commit your changes with a useful message in quotes.
3. Push your work to GitHub.

```shell
git add .
git commit -m "describe your change in quotes"
git push -u origin main
```

This will trigger the GitHub Actions workflow and publish your documentation via GitHub Pages.

### 3.6 Modify and Debug

With a working version safe in GitHub, start making changes to the code.

Before starting a new session, remember to do a `git pull` and keep your tools updated.

Each time forward progress is made, remember to git add-commit-push.


### 4.1 Run Python Scripts

To run Python scripts use:

```shell
uv run python -m analytics_project.demo_module_basics
```

---

## Campaign Performance Dashboard: Data Analysis Report

### Executive Summary

This analysis examines sales performance across 4 campaigns, generating $1.75M in total revenue with $171.91K in commission costs (6.72% average commission rate). The dashboard implements OLAP operations—slicing, dicing, and drill-down—to enable multi-dimensional business intelligence.

### Key Findings

#### 1. Campaign & Store Performance (Dicing Analysis)

The Campaign × Store matrix reveals significant performance variations:

- **Campaign 3.00** shows the strongest overall performance with $486,956 in total revenue
- **Store 404** is the top-performing location across most campaigns ($468,367 total)
- **Campaign 2.00 in Store 403** demonstrates the highest single combination revenue at $146,843 (highlighted in green)
- **Campaign 1.00 in Store 404** underperforms at $94,313 (highlighted in red), indicating a need for strategic review

**Business Insight**: Store 404's consistent strong performance suggests best practices that could be replicated across other locations. The Campaign 1.00 underperformance warrants investigation into campaign messaging, timing, or target audience alignment.

#### 2. Temporal Trends (Drill-Down Analysis)

The hierarchical time analysis (Year → Quarter → Month → Day) reveals:

- Revenue remains relatively stable across quarters from 2020-2024, hovering around 1.75M per quarter
- Q2 2022 shows a notable spike to approximately 1.8M, suggesting seasonal factors or successful initiatives
- The flat trend line indicates consistent market presence but limited growth momentum
- Single-day analysis (5/4/2025) shows concentrated activity, confirming operational focus

**Business Insight**: The plateau in quarterly revenue suggests market saturation or missed growth opportunities. The Q2 2022 spike should be analyzed to identify replicable success factors.

#### 3. Commission Efficiency (Slicing Analysis)

Using the campaign and store slicers to isolate performance:

- 6.72% average commission represents a standardized cost structure
- Total commission cost of $171.91K on $1.75M revenue yields approximately 10:1 revenue-to-commission ratio
- Individual campaign analysis shows commission rates vary slightly, suggesting negotiated or tiered structures

**Business Insight**: The commission structure appears sustainable, but opportunities may exist to optimize rates based on performance tiers or volume thresholds.

### OLAP Operations Implementation

#### Slicing

Three interactive slicers enable dimensional filtering:

- **Campaign Slicer**: Isolates specific campaign performance
- **Store Slicer**: Filters by location
- **Date Range Slicer**: Enables custom temporal analysis

**Use Case**: Marketing managers can slice data to "Campaign 2 in Store 403 during Q2" to evaluate targeted initiatives.

#### Dicing

The Campaign × Store matrix provides simultaneous two-dimensional analysis with heatmap visualization:

- Green cells indicate high-performing combinations (>$140K)
- Red cells flag underperforming pairs (<$95K)
- Row/column totals enable comparative analysis across dimensions

**Use Case**: Identify which campaign-store combinations warrant increased investment versus reallocation.

#### Drill-Down

Hierarchical date navigation (Year → Quarter → Month → Day) enables progressive granularity:

- **Year level**: Strategic overview of annual trends
- **Quarter level**: Seasonal pattern identification
- **Month level**: Campaign timing optimization
- **Day level**: Operational detail for specific events

**Use Case**: Executive stakeholders start with yearly trends, while operations teams drill to daily transaction patterns.

### Recommendations

1. **Replicate Store 404 Success**: Conduct operational audit to identify transferable best practices to stores 401-403
2. **Investigate Campaign 1.00 Underperformance**: Analyze messaging, audience targeting, and timing to improve ROI, particularly in Store 404 where the gap is most pronounced
3. **Capitalize on Q2 Opportunities**: Replicate Q2 2022 strategies that drove the revenue spike; investigate seasonal factors
4. **Drive Growth**: The flat revenue trend indicates need for market expansion, new campaign strategies, or customer acquisition initiatives to break the plateau
5. **Optimize Campaign-Store Matching**: Use the dicing matrix to reallocate marketing spend toward green (high-performing) combinations and either fix or discontinue red (underperforming) pairs

### Conclusion

This multi-dimensional analysis demonstrates that while overall revenue is stable at $1.75M, significant optimization opportunities exist at the campaign-store intersection level. The drill-down capability reveals temporal stability with isolated spikes, while slicing operations enable focused investigation of specific business scenarios. Strategic reallocation based on the dicing matrix insights could improve overall ROI without increasing total spend.
