import re
import pandas as pd
import mock_llm
import json
import random
import time

# Zero-shot system prompt
ZERO_SHOT_PROMPT = """
CLASSIFY the customer support ticket into exactly one category:
billing, delivery, technical, fraud.

Return JSON only in this format:
{"category": "...", "reason": "..."}
Do not include markdown or additional text.
"""

# Few-shot system prompt
FEW_SHOT_PROMPT = """
CLASSIFY the customer support ticket into exactly one category:
billing, delivery, technical, fraud.

Return JSON only in this format:
{"category": "...", "reason": "..."}
Do not include markdown or additional text.

EXAMPLES:
Ticket: I was charged twice for my order.
{"category": "billing", "reason": "Duplicate charge reported."}

Ticket: Someone accessed my account without permission.
{"category": "fraud", "reason": "Possible unauthorized account access."}

Ticket: My app crashes whenever I open it.
{"category": "technical", "reason": "Application crash reported."}
"""

# Configuration
MAX_INPUT_TOKENS = 400
BASE_DELAY = 0.05
MAX_RETRIES = 3

# Exact PII patterns required by the assignment
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_PATTERN = re.compile(r"\b[6-9]\d{9}\b")
ORDER_PATTERN = re.compile(r"ORD-\d{6}")

# Load tickets without converting empty strings to NaN
tickets = pd.read_csv(
    "data/raw/tickets.csv",
    keep_default_na=False
)

# Redact personal information
def redact_pii(text):
    text, email_count = EMAIL_PATTERN.subn("[EMAIL]", text)
    text, phone_count = PHONE_PATTERN.subn("[PHONE]", text)
    text, order_count = ORDER_PATTERN.subn("[ORDER_ID]", text)

    return text, email_count, phone_count, order_count


# Prepare tickets and count redactions
prepared_tickets = []
email_total = 0
phone_total = 0
order_total = 0

for _, ticket in tickets.iterrows():
    original_text = ticket["text"]

    redacted_text, emails, phones, orders = redact_pii(
        original_text
    )

    email_total += emails
    phone_total += phones
    order_total += orders

    # Input guardrails
    if not original_text.strip():
        status = "skipped_empty"
    elif mock_llm.est_tokens(original_text) > MAX_INPUT_TOKENS:
        status = "flagged_long"
    else:
        status = "eligible"

    prepared_tickets.append({
        "ticket_id": ticket["ticket_id"],
        "customer_id": ticket["customer_id"],
        "order_id": ticket["order_id"],
        "text": original_text,
        "redacted_text": redacted_text,
        "true_category": ticket["true_category"],
        "status": status
    })


# Verify that redaction removed all PII
for ticket in prepared_tickets:
    text = ticket["redacted_text"]

    assert not EMAIL_PATTERN.search(text)
    assert not PHONE_PATTERN.search(text)
    assert not ORDER_PATTERN.search(text)


# Summary
prepared_df = pd.DataFrame(prepared_tickets)

print("=== Ticket Input Guardrails ===")
print("Total tickets:", len(prepared_df))
print("Empty tickets:", (prepared_df["status"] == "skipped_empty").sum())
print("Long tickets:", (prepared_df["status"] == "flagged_long").sum())
print("Eligible tickets:", (prepared_df["status"] == "eligible").sum())

print("\n=== PII Redaction Summary ===")
print("Emails redacted:", email_total)
print("Phone numbers redacted:", phone_total)
print("Order IDs redacted:", order_total)
print("Total substitutions:", email_total + phone_total + order_total)

print("\nPII verification: PASSED")
print("Remaining PII matches: 0")

def call_with_retry(ticket_id, messages):
    for retry_number in range(MAX_RETRIES + 1):
        try:
            return mock_llm.chat(messages)

        except mock_llm.TransientLLMError:
            if retry_number == MAX_RETRIES:
                raise

            wait = (
                BASE_DELAY
                * (2 ** retry_number)
                * random.uniform(0.9, 1.15)
            )

            print(
                f"Retry: ticket={ticket_id}, "
                f"retry={retry_number}, wait={wait:.4f}s"
            )

            time.sleep(wait)

ALLOWED_CATEGORIES = {
    "billing",
    "delivery",
    "technical",
    "fraud"
}

def validate_response(response_text):
    # First try JSON validation
    try:
        result = json.loads(response_text)

        category = result.get("category")

        if category in ALLOWED_CATEGORIES:
            return category, "classified_json"

        return None, "flagged_invalid_output"

    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback: extract lowercase words
    words = re.findall(r"[a-z]+", response_text.lower())

    matches = ALLOWED_CATEGORIES.intersection(words)

    if len(matches) == 1:
        return matches.pop(), "classified_keyword"

    return None, "flagged_invalid_output"

def run_pipeline(system_prompt, token_budget=None):
    # Reset mock immediately before each independent run
    mock_llm.reset()

    results = []
    total_tokens = 0

    for ticket in prepared_tickets:

        result = {
            "ticket_id": ticket["ticket_id"],
            "customer_id": ticket["customer_id"],
            "status": ticket["status"],
            "category": "",
            "true_category": ticket["true_category"],
            "tokens_used": 0
        }

        # Skip empty and oversized tickets
        if ticket["status"] != "eligible":
            results.append(result)
            continue

        # Check token budget before making a model call
        if token_budget is not None and total_tokens >= token_budget:
            result["status"] = "budget_exhausted"
            results.append(result)
            continue

        # User message must contain ONLY redacted ticket text
        redacted_text = ticket["redacted_text"]

        # Privacy assertions before model call
        assert not EMAIL_PATTERN.search(redacted_text)
        assert not PHONE_PATTERN.search(redacted_text)
        assert not ORDER_PATTERN.search(redacted_text)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": redacted_text}
        ]

        # Call model with retry protection
        response = call_with_retry(
            ticket["ticket_id"],
            messages
        )

        response_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        total_tokens += tokens_used

        # Validate model response
        category, status = validate_response(response_text)

        result["category"] = category or ""
        result["status"] = status
        result["tokens_used"] = tokens_used

        results.append(result)

    results_df = pd.DataFrame(results)

    classified = results_df[
        results_df["status"].isin([
            "classified_json",
            "classified_keyword"
        ])
    ]

    correct = (
        classified["category"] == classified["true_category"]
    ).sum()

    accuracy = (
        correct / len(classified) * 100
        if len(classified) > 0 else 0
    )

    tokens_per_ticket = (
        total_tokens / len(classified)
        if len(classified) > 0 else 0
    )

    print("\n=== Classification Summary ===")
    print("Status counts:")
    print(results_df["status"].value_counts())

    print("\nTickets classified:", len(classified))
    print("Correct predictions:", correct)
    print("Accuracy:", round(accuracy, 2), "%")
    print("Total tokens:", total_tokens)
    print("Tokens per classified ticket:", round(tokens_per_ticket, 2))

    return results_df, total_tokens


# Run zero-shot classification
print("\n========== ZERO-SHOT RUN ==========")

zero_shot_results, zero_shot_tokens = run_pipeline(
    ZERO_SHOT_PROMPT
)

# Zero-shot confusion matrix
zero_classified = zero_shot_results[
    zero_shot_results["status"].isin([
        "classified_json",
        "classified_keyword"
    ])
]

confusion = pd.crosstab(
    zero_classified["true_category"],
    zero_classified["category"],
    rownames=["Actual"],
    colnames=["Predicted"]
).reindex(
    index=["billing", "delivery", "technical", "fraud"],
    columns=["billing", "delivery", "technical", "fraud"],
    fill_value=0
)

print("\n=== Zero-Shot Confusion Matrix ===")
print(confusion)


# Run few-shot classification
print("\n========== FEW-SHOT RUN ==========")

few_shot_results, few_shot_tokens = run_pipeline(
    FEW_SHOT_PROMPT
)

# Run zero-shot classification with token budget
print("\n========== TOKEN BUDGET DEMO ==========")

TOKEN_BUDGET = 6000

budget_results, budget_total_tokens = run_pipeline(
    ZERO_SHOT_PROMPT,
    token_budget=TOKEN_BUDGET
)

# Count tickets stopped by the budget
budget_exhausted_count = (
    budget_results["status"] == "budget_exhausted"
).sum()

# Save budget demonstration output
budget_results.to_csv(
    "outputs/triage_budget_demo.csv",
    index=False
)

print("\n=== Budget Demo Summary ===")
print("Token budget:", TOKEN_BUDGET)
print("Tokens consumed:", budget_total_tokens)
print("Budget exhausted tickets:", budget_exhausted_count)
print("Saved: outputs/triage_budget_demo.csv")

# Final few-shot run with customer segment-based routing
print("\n========== FINAL TRIAGE RUN ==========")

FINAL_TOKEN_BUDGET = 100000

final_results, final_total_tokens = run_pipeline(
    FEW_SHOT_PROMPT,
    token_budget=FINAL_TOKEN_BUDGET
)

# Load customer segments
segments = pd.read_csv("outputs/customer_segments.csv")

segment_lookup = segments[
    ["customer_id", "segment_name", "is_premium"]
]

# Attach customer segment information
final_results = final_results.merge(
    segment_lookup,
    on="customer_id",
    how="left"
)

final_results["segment_name"] = (
    final_results["segment_name"].fillna("")
)

final_results["is_premium"] = (
    final_results["is_premium"].fillna(False).astype(bool)
)

# Apply routing and priority rules
human_review_statuses = {
    "skipped_empty",
    "flagged_long",
    "flagged_invalid_output",
    "budget_exhausted"
}

def assign_routing(row):
    if row["status"] in human_review_statuses:
        return "human_review", "NORMAL"

    if row["category"] == "fraud":
        return "security_team", "HIGH"

    if row["is_premium"]:
        return "premium_desk", "HIGH"

    return "support_queue", "NORMAL"


final_results[["route", "priority"]] = final_results.apply(
    lambda row: pd.Series(assign_routing(row)),
    axis=1
)

# Keep only the required output columns
final_output = final_results[
    [
        "ticket_id",
        "customer_id",
        "status",
        "category",
        "segment_name",
        "priority",
        "route",
        "tokens_used"
    ]
].copy()

final_output["category"] = final_output["category"].fillna("")

# Save final results
final_output.to_csv(
    "outputs/triage_results.csv",
    index=False
)

# Validate output
assert len(final_output) == 164
assert list(final_output.columns) == [
    "ticket_id",
    "customer_id",
    "status",
    "category",
    "segment_name",
    "priority",
    "route",
    "tokens_used"
]

print("\n=== Final Triage Summary ===")
print("Total tickets:", len(final_output))
print("Total tokens:", final_total_tokens)

print("\nStatus counts:")
print(final_output["status"].value_counts())

print("\nRouting counts:")
print(final_output["route"].value_counts())

print("\nPriority counts:")
print(final_output["priority"].value_counts())

print("\nSaved: outputs/triage_results.csv")