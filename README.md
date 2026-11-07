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


## Part B – Customer Segments and Lapse Prediction

### 1. RFM Analysis

Built an RFM table using completed orders for 1,175 customers.

- **Recency:** Days since the customer's last completed order, calculated relative to 1 October 2025.
- **Frequency:** Number of completed orders.
- **Monetary:** Total completed order amount in INR.

| Metric | Recency | Frequency | Monetary (INR) |
|---|---:|---:|---:|
| Mean | 33.56 | 9.46 | 2,552.06 |
| Median | 19 | 5 | 2,286.50 |
| Minimum | 0 | 1 | 12.00 |
| Maximum | 180 | 33 | 14,766.55 |

### 2. Customer Segmentation

Applied StandardScaler to the RFM features and evaluated K-Means for K values from 2 to 8, using inertia and silhouette scores.

Selected **K = 4** because it achieved the highest silhouette score (0.526) among the tested values, with a useful balance between cluster separation and business interpretability.

| K | Inertia | Silhouette |
|---:|---:|---:|
| 2 | 1820.76 | 0.465 |
| 3 | 1268.23 | 0.445 |
| 4 | 743.07 | 0.526 |
| 5 | 617.37 | 0.480 |
| 6 | 503.17 | 0.482 |
| 7 | 408.46 | 0.416 |
| 8 | 366.50 | 0.412 |

#### Segment Profiles

| Segment | Customers | Avg. Recency | Avg. Frequency | Avg. Monetary (INR) | Business Interpretation |
|---|---:|---:|---:|---:|---|
| 0 | 436 | 28.86 | 3.77 | 1,057.62 | Occasional Customers |
| 1 | 138 | 24.12 | 6.77 | 7,129.70 | Premium Customers |
| 2 | 419 | 8.77 | 19.40 | 3,410.02 | Loyal Customers |
| 3 | 182 | 109.04 | 2.20 | 685.99 | At-Risk Customers |

Premium customers were identified using segment 1, resulting in 138 premium customers.

#### PCA Analysis

Applied PCA to the scaled RFM features to reduce them to two dimensions.

| Component | Explained Variance |
|---|---:|
| Principal Component 1 | 0.634 |
| Principal Component 2 | 0.218 |
| Total | 0.852 |

The first two components retain 85.2% of the variance in the original RFM features.

### 3. Lapse Prediction Dataset

Created a customer-level prediction dataset using 1 September 2025 as the cutoff date.

- Customers were included if they had at least one completed order before the cutoff.
- A customer was labelled as lapsed (1) if they had no completed order during September 2025.
- A customer was labelled as not lapsed (0) if they had at least one completed order during September 2025.
- Prediction features were calculated using historical information before the cutoff date.

| Metric | Result |
|---|---:|
| Total customers | 1,156 |
| Lapsed customers | 443 |
| Not-lapsed customers | 713 |
| Lapse percentage | 38.32% |

All generated prediction features had zero missing values.

### 4. Model Training and Evaluation

Used a stratified 80/20 train-test split with random_state=42.

- Training customers: 924
- Testing customers: 232
- Numerical features were scaled using StandardScaler.
- Categorical features were encoded using OneHotEncoder with drop-first encoding.
- Preprocessing was fitted within the model pipeline, using training data only.

#### Baseline Model

The baseline predicted every customer as not lapsed.

| Metric | Score |
|---|---:|
| Accuracy | 0.616 |
| Precision | 0.000 |
| Recall | 0.000 |
| F1 Score | 0.000 |

The baseline failed to identify any lapsed customers, demonstrating why accuracy alone is insufficient.

#### Model Comparison

Logistic Regression was tuned using GridSearchCV over C values [0.01, 0.1, 1, 10, 100].

Random Forest was tuned over max_depth [3, 5, 8] and min_samples_leaf [5, 10, 20].

Both models used 5-fold cross-validation with F1 scoring.

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Best Parameters | C = 100 | Depth = 5, Leaf = 10 |
| Cross-validation F1 | 0.651 | 0.684 |
| Test Accuracy | 0.728 | 0.720 |
| Test Precision | 0.644 | 0.630 |
| Test Recall | 0.652 | 0.652 |
| Test F1 | 0.648 | 0.641 |

The original Logistic Regression model was selected over Random Forest because it achieved slightly higher test F1, precision, and accuracy on the untouched test set.

#### Oversampling Experiment

The training dataset was balanced by randomly oversampling the lapsed class with replacement. The test dataset remained unchanged.

Balanced training distribution:

- Not-lapsed: 570
- Lapsed: 570

| Metric | Before Oversampling | After Oversampling |
|---|---:|---:|
| Accuracy | 0.728 | 0.720 |
| Precision | 0.644 | 0.600 |
| Recall | 0.652 | 0.809 |
| F1 Score | 0.648 | 0.689 |

Oversampling improved recall and F1, identifying more potentially lapsed customers. However, precision decreased, resulting in more false-positive retention targets.

The original Logistic Regression model was retained as the selected model because it offered higher precision and fewer false positives for the illustrative retention list. The oversampled model is retained as a comparison experiment.

### 5. Feature Interpretation

#### Top Random Forest Features

| Feature | Importance |
|---|---:|
| Frequency | 0.3533 |
| Monetary | 0.2279 |
| Recency | 0.0973 |
| Cancellation Rate | 0.0951 |
| Average Discount | 0.0508 |

Frequency and monetary value were the most influential features in the Random Forest model.

#### Logistic Regression Coefficients

Selected examples:

| Feature | Coefficient | Interpretation |
|---|---:|---|
| Frequency | -1.6986 | Higher frequency is associated with lower lapse probability. |
| Electronics category | -0.9869 | Lower lapse probability relative to the reference category. |
| Delhi city | -0.6406 | Lower lapse probability relative to the reference city. |

Positive coefficients indicate an association with higher lapse probability, while negative coefficients indicate an association with lower lapse probability. These coefficients do not establish causation.

### 6. Premium Customer Retention List

Used the selected Logistic Regression model to calculate lapse probabilities for premium customers in the test set.

| Metric | Result |
|---|---:|
| Premium customers in test set | 40 |
| Customers shortlisted | 10 |
| Highest predicted lapse probability | 72.76% |
| Actually lapsed among top 10 | 2 |

The top 10 customers were ranked by predicted lapse probability and saved to `outputs/retention_list.csv`.

### 7. Generated Outputs

- `outputs/rfm.csv`
- `outputs/customer_segments.csv`
- `outputs/lapse_dataset.csv`
- `outputs/lapse_model.joblib`
- `outputs/retention_list.csv`

The saved model was reloaded and tested. Its predictions were identical to those of the original model.

### Limitations

- The premium segment was generated using full-period RFM information, including data after the lapse prediction cutoff. Therefore, the premium retention list is illustrative and is not a leakage-free evaluation of premium targeting.
- The dataset is synthetic and may not represent real customer behaviour.
- Oversampling improves recall but reduces precision, which may increase retention campaign costs.
- Feature importance and model coefficients indicate associations, not causation.


## Part C — Support Ticket Triage with Guardrails

### 1. Input Guardrails

Processed 164 support tickets:
- Empty tickets: 4 — skipped with `skipped_empty`.
- Long tickets: 4 — flagged with `flagged_long`.
- Eligible tickets: 156.

Empty and long tickets were never sent to the mock LLM.

### 2. PII Redaction

Applied regular-expression redaction in the required order:
1. Email addresses → `[EMAIL]`
2. Phone numbers → `[PHONE]`
3. Order IDs → `[ORDER_ID]`

| PII type | Values redacted |
|---|---:|
| Emails | 55 |
| Phone numbers | 91 |
| Order IDs | 132 |
| **Total substitutions** | **278** |

PII verification passed, with zero remaining matches.

### 3. Zero-shot vs Few-shot Classification

Both prompts instructed the model to classify tickets into billing, delivery, technical, or fraud and return JSON-only output.

| Metric | Zero-shot | Few-shot |
|---|---:|---:|
| Classified tickets | 147 | 147 |
| Correct predictions | 126 | 147 |
| Accuracy | 85.71% | 100% |
| Total tokens | 10,492 | 19,228 |
| Tokens per classified ticket | 71.37 | 130.80 |

Few-shot prompting improved accuracy by 14.29 percentage points and corrected 21 additional predictions.

The few-shot approach consumed 8,736 additional tokens, approximately 59.43 more tokens per classified ticket.

### 4. Response Validation and Retry Handling

Responses were validated as JSON with an allowed category. If JSON validation failed, a keyword fallback accepted a response only when exactly one allowed category was detected. Invalid or unsupported responses were flagged for human review rather than guessed.

Final few-shot status counts:

| Status | Tickets |
|---|---:|
| classified_json | 135 |
| classified_keyword | 12 |
| flagged_invalid_output | 9 |
| skipped_empty | 4 |
| flagged_long | 4 |
| **Total** | **164** |

The mock LLM was reset before each complete run. Transient failures were retried with exponential backoff and jitter, with a maximum of three retries per ticket. All 19 transient errors recovered successfully during each run.

### 5. Token Budget Demonstration

Ran zero-shot classification with a token budget of 6,000.

| Metric | Result |
|---|---:|
| Configured budget | 6,000 |
| Tokens consumed | 6,052 |
| Classified tickets | 85 |
| Budget-exhausted tickets | 66 |

The final permitted model call took the running total to 6,052. Subsequent tickets were marked `budget_exhausted` without further model calls.

### 6. Customer-based Routing

The final few-shot results were joined with customer segment information.

Routing rules:
- Empty, long, invalid-output, or budget-exhausted tickets → `human_review`, NORMAL.
- Fraud tickets → `security_team`, HIGH.
- Premium customers → `premium_desk`, HIGH.
- Other valid tickets → `support_queue`, NORMAL.

| Route | Tickets |
|---|---:|
| support_queue | 102 |
| security_team | 34 |
| human_review | 17 |
| premium_desk | 11 |
| **Total** | **164** |

Priority distribution:
- HIGH: 45
- NORMAL: 119

### 7. Output Files

- `triage_tickets.py` — ticket processing, redaction, classification, validation, retries, budget enforcement, and routing.
- `outputs/triage_results.csv` — final 164-ticket classification and routing results.
- `outputs/triage_budget_demo.csv` — zero-shot token budget demonstration.

### 8. Limitations

- Classification uses the supplied offline mock LLM, not a production language model.
- Few-shot prompting improves accuracy in this evaluation but requires more tokens.
- Invalid model responses are routed to human review.
- Regular-expression redaction depends on the supported PII patterns and may not identify every possible sensitive-data format.
- The token budget is checked before each model call, so a permitted call can cause the running total to exceed the configured limit.


## Part D – Policy RAG Assistant and Refund Agent

### 1. Policy Document Chunking

Loaded five policy text files from `data/policies/` and split them into chunks of 40 words with a 10-word overlap.

| Policy document | Chunks |
|---|---:|
| Refund | 4 |
| Delivery | 3 |
| Escalation | 3 |
| Payment | 3 |
| Privacy | 2 |
| **Total** | **15** |

The overlap preserves context between consecutive chunks and reduces the chance of splitting important policy information across chunk boundaries.

### 2. TF-IDF Retrieval

Implemented document retrieval using Scikit-learn's `TfidfVectorizer` and cosine similarity.

- **Term Frequency (TF):** Measures how frequently a word appears in a document.
- **Inverse Document Frequency (IDF):** Gives more importance to words that are less common across the documents.
- **Cosine Similarity:** Measures similarity between the question vector and policy chunk vectors.

The `retrieve(query, k=3)` function returns the three most relevant policy chunks, including their source filenames and similarity scores.

**Limitation:** TF-IDF relies on word matching. It may not understand synonyms, context, or semantic similarity as effectively as embedding-based retrieval.

### 3. Retrieval-Augmented Generation (RAG)

Implemented an `answer(question)` function that:

1. Retrieves the top three relevant policy chunks.
2. Builds a context containing source filenames and chunk text.
3. Sends the context and question to the mock LLM.
4. Instructs the model to answer only using the supplied policy context.
5. Returns a fallback response when the required information is unavailable.

The system prompt identifies the model as a `POLICY ASSISTANT` and restricts answers to the supplied policy context.

Fallback response:

`I could not find the information in the supplied policies.`

### 4. Policy Retrieval Evaluation

Evaluated the policy assistant using `data/raw/policy_eval.csv`, containing 14 questions:

- 12 answerable questions.
- 2 unanswerable questions.

The evaluation checks:

- Whether the expected policy document appears in the retrieved top three chunks.
- Whether the expected fact appears in the generated answer.
- Whether unanswerable questions receive the expected fallback response.

Compared two chunking configurations:

| Configuration | Chunk size | Overlap |
|---|---:|---:|
| Normal chunking | 40 words | 10 words |
| Zero-overlap chunking | 40 words | 0 words |

#### Evaluation Results

| Metric | 10-word overlap | Zero overlap |
|---|---:|---:|
| Answerable retrieval hits | 12/12 | 12/12 |
| Expected facts found | 12/12 | 10/12 |
| Unanswerable fallback hits | 2/2 | 2/2 |

#### Observations

- With 10-word overlap, all 12 answerable questions returned the expected facts.
- With zero overlap, retrieval still found all 12 expected policy documents, but only 10 expected facts were found.
- Two expected facts were missed without overlap, demonstrating how important information can be split across chunk boundaries.
- Both configurations correctly handled the two unanswerable questions using the fallback response.

**Conclusion:** The 10-word overlap configuration achieved 100% expected-fact accuracy in this evaluation, compared with 83.33% for zero overlap.

### 5. Refund Agent Tools

Implemented five tools for the customer refund workflow.

| Tool | Responsibility |
|---|---|
| `get_order` | Retrieves order details from SQLite. |
| `search_policy` | Searches the policy documents. |
| `calculate_refund` | Calculates the eligible refund amount. |
| `issue_refund` | Records an approved refund in the refund ledger. |
| `escalate_to_human` | Records refunds requiring human approval. |

Defined tool specifications in `TOOLS_SPEC` and mapped tool names to their Python implementations using `TOOL_MAP`.

Refund calculation follows the delivery policy. Refunds above INR 1,000 require human approval.

### 6. ReAct Agent Implementation

Implemented a ReAct-style agent using the mock LLM.

The agent follows an iterative workflow:

1. Receives a customer request.
2. Calls the appropriate tool.
3. Observes the tool result.
4. Uses the observation to decide the next action.
5. Continues until it produces a final response or reaches a safety limit.

#### Safety Controls

| Control | Configuration |
|---|---:|
| Maximum iterations | 6 |
| Token limit | 6,000 |
| Time limit | 10 seconds |
| Checkpoint frequency | After every tool observation |

The agent supports fallback responses for:

- `FALLBACK_TOKEN_LIMIT`
- `FALLBACK_TIMEOUT`
- `FALLBACK_MAX_ITERATIONS`

### 7. Agent Scenario Evaluation

Executed all seven supplied agent scenarios using `test_agent.py`.

| Scenario | Final status | LLM calls | Tokens used |
|---|---|---:|---:|
| S1 | REFUND | 5 | 1,073 |
| S2 | REFUND | 5 | 1,073 |
| S3 | ESCALATE | 5 | 1,060 |
| S4 | DENIED | 4 | 738 |
| S5 | DENIED | 3 | 431 |
| S6 | NOT_FOUND | 2 | 131 |
| S7 | FALLBACK_MAX_ITERATIONS | 6 | 3,228 |

The agent generated the scenario results in `outputs/agent_runs.jsonl`.

Refund and escalation actions were recorded in `outputs/refund_ledger.jsonl`.

### 8. Token Limit and Timeout Demonstrations

#### Token Limit Demonstration

Configured a token limit of 200.

| Metric | Result |
|---|---|
| Status | FALLBACK_TOKEN_LIMIT |
| LLM calls | 3 |
| Tools executed | 2 |
| Tokens before fallback | 161 |

The agent stopped before executing a tool call that would exceed the configured token budget.

#### Timeout Demonstration

Configured the time limit as zero seconds.

| Metric | Result |
|---|---|
| Status | FALLBACK_TIMEOUT |
| LLM calls | 0 |
| Tools executed | 0 |

The agent checked the elapsed time before making its first model call and returned the timeout fallback.

### 9. Checkpoint and Resume Demonstration

Implemented checkpointing to save the agent's state after every tool observation.

The checkpoint stores:

- Conversation messages.
- Executed tools and their observations.
- Number of LLM calls.
- Tokens used.
- Iteration count.
- Execution steps.

Simulated a crash after the second tool execution, after saving the checkpoint.

Resumed the agent using the saved checkpoint.

#### Resume Results

| Metric | Result |
|---|---|
| Final status | REFUND |
| Refund amount | INR 128.25 |
| LLM calls | 5 |
| Tokens used | 1,073 |

**Resumed tool execution order:**

`get_order → search_policy → calculate_refund → issue_refund`

The agent continued from the saved state without repeating the first two tool executions.

### 10. ReAct vs Plan-and-Execute

ReAct performs reasoning and tool execution iteratively. It uses each tool observation to determine the next action. In this implementation, model calls varied by scenario: S1 required 5 calls, S5 required 3, and S6 required 2.

Plan-and-execute separates planning from execution. It creates a plan first and then executes the planned steps. This can make workflows more predictable, but unexpected tool observations may require replanning.

For this project, ReAct was selected because refund decisions depend on order details and policy results. The agent can use each observation before deciding whether to calculate a refund, issue it, or escalate it.

The model-call figures above are measured for ReAct. A separate plan-and-execute benchmark was not implemented.

### 11. Generated Outputs

- `policy_rag.py` – policy chunking, TF-IDF retrieval, RAG evaluation, refund tools, and agent implementation.
- `test_agent.py` – executes the seven agent scenarios.
- `outputs/agent_runs.jsonl` – agent scenario results.
- `outputs/refund_ledger.jsonl` – refund and escalation records.
- `state/` – saved agent checkpoints.

### 12. Limitations and Next Steps

- The project uses an offline mock LLM rather than a production LLM.
- TF-IDF retrieval relies on word matching and does not provide semantic understanding.
- The policy evaluation dataset contains only 14 questions.
- The refund workflow uses predefined business rules and a sample SQLite database.
- The time limit is checked between model calls; an individual model call may take longer than the configured limit.
- A production implementation would benefit from embedding-based retrieval, a real LLM, stronger tool validation, and persistent checkpoint storage.