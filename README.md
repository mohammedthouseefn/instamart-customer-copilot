## Part A – Data Foundation: Clean, Store, Query

### 1. Raw Data Audit

The raw datasets were loaded using Pandas before cleaning.

#### Dataset overview

| Dataset | Rows | Columns |
|---|---:|---:|
| Customers | 1,200 | 5 |
| Products | 40 | 4 |
| Orders | 13,084 | 9 |

#### Data types and missing values

**Customers**

| Column | Data type | Missing count | Missing % |
|---|---|---:|---:|
| customer_id | str | 0 | 0.00% |
| city | str | 0 | 0.00% |
| signup_date | str | 0 | 0.00% |
| age | float64 | 61 | 5.08% |
| gender | str | 30 | 2.50% |

**Products**

| Column | Data type | Missing count | Missing % |
|---|---|---:|---:|
| product_id | str | 0 | 0.00% |
| product_name | str | 0 | 0.00% |
| category | str | 0 | 0.00% |
| price_inr | int64 | 0 | 0.00% |

**Orders**

| Column | Data type | Missing count | Missing % |
|---|---|---:|---:|
| order_id | str | 0 | 0.00% |
| customer_id | str | 0 | 0.00% |
| product_id | str | 0 | 0.00% |
| quantity | int64 | 0 | 0.00% |
| order_ts | str | 0 | 0.00% |
| status | str | 0 | 0.00% |
| discount_pct | int64 | 0 | 0.00% |
| order_amount | str | 53 | 0.41% |
| delivery_minutes | float64 | 2,541 | 19.42% |

#### Raw data audit findings

| Audit metric | Count |
|---|---:|
| Raw order rows | 13,084 |
| Exact duplicate rows | 119 |
| Pending orders | 656 |
| Distinct order IDs | 12,309 |
| Non-numeric order amounts | 120 |
| Negative delivery times | 106 |
| Blank delivery times | 2,541 |
| Blank customer ages | 61 |
| Ages outside 10–100 | 6 |
| Distinct raw city spellings | 24 |
| Distinct non-blank gender spellings | 10 |
| Blank genders | 30 |

### 2. Data Cleaning

#### Customer cleaning

- Removed leading/trailing spaces from city names and applied title case.
- Standardised gender values to `male`, `female`, or `unknown`.
- Converted ages outside 10–100 to missing values.
- Filled missing ages using the median age of the corresponding city with `groupby()` and `transform()`.
- Converted `signup_date` to datetime.

**Results after cleaning:**

| Metric | Result |
|---|---:|
| Customers | 1,200 |
| Bengaluru | 197 |
| Chennai | 191 |
| Delhi | 210 |
| Hyderabad | 191 |
| Mumbai | 184 |
| Pune | 227 |
| Female | 610 |
| Male | 560 |
| Unknown | 30 |
| Missing ages | 0 |
| Age range | 18–60 |

#### Order cleaning

The following rules were applied in order:

1. Converted `order_ts` to datetime.
2. Removed 119 exact duplicate rows (13,084 → 12,965).
3. Removed duplicate `order_id` records by retaining the latest `order_ts` (12,965 → 12,309).
4. Converted `order_amount` to numeric and replaced unparseable values with missing values.
5. Filled missing order amounts using product price, quantity and discount:

   `order_amount = round(price_inr * quantity * (1 - discount_pct / 100), 2)`

6. Converted negative `delivery_minutes` values to missing.
7. Filled missing delivery times for completed orders using the median delivery time of the corresponding product category, with `groupby()` and `transform()`.
8. Left cancelled orders' delivery times missing because cancelled orders were never delivered.

**Results after cleaning:**

| Metric | Result |
|---|---:|
| Total orders | 12,309 |
| Completed orders | 11,110 |
| Cancelled orders | 1,199 |
| Pending orders | 0 |
| Missing order amounts | 0 |
| Missing delivery times in completed orders | 0 |
| Missing delivery times in cancelled orders | 1,199 |
| Completed-order revenue | INR 2,998,668.80 |

### 3. SQLite Database and Validation

Cleaned datasets were saved as CSV files:

- `data/clean/customers.csv`
- `data/clean/products.csv`
- `data/clean/orders.csv`

The datasets were also stored in `data/instamart.db` with three tables:

| Table | Rows |
|---|---:|
| customers | 1,200 |
| products | 40 |
| orders | 12,309 |

The validation script checked 17 data-quality checkpoints. All passed.

**Validation result:** `ALL CHECKPOINTS PASSED`

### 4. SQL Analysis

Seven SQL queries were implemented in `sql/queries.sql` and executed against the SQLite database using Pandas `read_sql_query()`.

| Query | SQL concept | Result |
|---|---|---:|
| Q1 | WHERE and HAVING | 30 customers |
| Q2 | Three-table JOIN | 30 city/category combinations |
| Q3 | Scalar subquery | 11 products |
| Q4 | LEFT JOIN | 25 customers |
| Q5 | Common Table Expressions (CTEs) | 550 customers |
| Q6 | RANK, DENSE_RANK and ROW_NUMBER | 1,175 customers |
| Q7 | Running total using a window function | 183 daily rows |

Additional SQL findings:

- Q2 total completed revenue: INR 2,998,668.80.
- Highest city/category revenue: Bengaluru / Electronics – INR 233,909.45.
- Q5 average customer spend: INR 2,552.06.
- Q6 top customers by city:
  - Bengaluru: C0082 – INR 12,856.20
  - Chennai: C0930 – INR 10,151.40
  - Delhi: C0291 – INR 13,742.60
  - Hyderabad: C0743 – INR 12,730.05
  - Mumbai: C0693 – INR 14,766.55
  - Pune: C0426 – INR 10,377.10
- Q6 produced 8 rows where RANK differs from ROW_NUMBER because tied values share the same rank, while ROW_NUMBER assigns a unique sequential number.
- Q7 final cumulative revenue: INR 2,998,668.80.

### 5. Pandas Cross-Check and Exploratory Data Analysis

The Q2 revenue analysis was independently rebuilt using `pd.pivot_table()` with `margins=True`.

| Check | Revenue |
|---|---:|
| SQL total | INR 2,998,668.80 |
| Pandas total | INR 2,998,668.80 |

The city-level aggregation was also verified using Pandas `groupby()` and named aggregation.

#### Completed order amount statistics

| Statistic | Value |
|---|---:|
| Mean | INR 269.91 |
| Median | INR 135.00 |
| Skewness | 4.61 |
| Q1 | INR 64.80 |
| Q3 | INR 297.00 |
| IQR | INR 232.20 |
| Lower fence | INR -283.50 |
| Upper fence | INR 645.30 |
| Outliers below lower fence | 0 |
| Outliers above upper fence | 897 |

#### Correlation analysis

The correlation matrix was calculated using `order_amount`, `discount_pct`, `quantity`, and `delivery_minutes` for completed orders.

The strongest absolute correlation was between `order_amount` and `discount_pct`, at approximately -0.095. This is a very weak negative correlation. Correlation of this size does not establish causation.

#### EDA observations

The data represents completed customer orders across six cities and five product categories. Order amounts are strongly right-skewed, with a mean of INR 269.91 and a median of INR 135.00. The analysis identified 897 high-value outliers above the upper IQR fence and no outliers below the lower fence. The strongest absolute relationship was a weak negative correlation between order amount and discount percentage (-0.095); this does not establish causation.