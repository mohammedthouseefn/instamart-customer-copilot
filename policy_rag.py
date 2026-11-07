import os
import mock_llm
import pandas as pd
import sqlite3
import json
import time
from datetime import datetime, timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

POLICY_DIR = "data/policies"

def chunk_document(text, chunk_size=40, overlap=10):
    words = text.split()
    chunks = []

    step = chunk_size - overlap

    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]

        if not chunk_words:
            break

        chunks.append(" ".join(chunk_words))

        if start + chunk_size >= len(words):
            break

    return chunks


def load_policy_documents(overlap=10):
    all_chunks = []

    for filename in sorted(os.listdir(POLICY_DIR)):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(POLICY_DIR, filename)

        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        chunks = chunk_document(text, overlap=overlap)

        for chunk in chunks:
            all_chunks.append({
                "source": filename,
                "text": chunk
            })

    return all_chunks

# Build TF-IDF index
policy_chunks = load_policy_documents()

vectorizer = TfidfVectorizer()

chunk_texts = [chunk["text"] for chunk in policy_chunks]

tfidf_matrix = vectorizer.fit_transform(chunk_texts)


def retrieve(query, k=3):
    query_vector = vectorizer.transform([query])

    similarities = cosine_similarity(
        query_vector,
        tfidf_matrix
    ).flatten()

    top_indices = similarities.argsort()[::-1][:k]

    results = []

    for index in top_indices:
        results.append({
            "source": policy_chunks[index]["source"],
            "score": float(similarities[index]),
            "text": policy_chunks[index]["text"]
        })

    return results

def answer(question):
    retrieved_chunks = retrieve(question, k=3)

    context = "\n".join(
        f"[{chunk['source']}]\n{chunk['text']}"
        for chunk in retrieved_chunks
    )

    system_message = {
        "role": "system",
        "content": (
            "You are a POLICY ASSISTANT. "
            "Answer questions only using the supplied policy context. "
            "If the information is not available in the context, "
            "say: I could not find the information in the supplied policies."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"CONTEXT:\n{context}\n"
            f"QUESTION:\n{question}"
        )
    }

    response = mock_llm.chat([
        system_message,
        user_message
    ])

    answer_text = response.choices[0].message.content

    sources = list(dict.fromkeys(
        chunk["source"] for chunk in retrieved_chunks
    ))

    return {
        "answer": answer_text,
        "sources": sources
    }

def evaluate_policy(chunks, label):
    global policy_chunks, vectorizer, tfidf_matrix

    policy_chunks = chunks

    vectorizer = TfidfVectorizer()
    chunk_texts = [chunk["text"] for chunk in policy_chunks]
    tfidf_matrix = vectorizer.fit_transform(chunk_texts)

    evaluation = pd.read_csv("data/raw/policy_eval.csv")

    retrieval_hits = 0
    fact_hits = 0
    fallback_hits = 0

    failures = []

    for _, row in evaluation.iterrows():
        question = row["question"]
        expected_doc = row["expected_doc"]
        expected_fact = row["expected_fact"]

        retrieved = retrieve(question, k=3)
        result = answer(question)

        sources = [item["source"] for item in retrieved]
        response = result["answer"]

        if expected_doc != "NONE":
            if expected_doc in sources:
                retrieval_hits += 1
            else:
                failures.append(question)

            if (
                pd.notna(expected_fact)
                and expected_fact in response
            ):
                fact_hits += 1

        else:
            if response.startswith("I could not find"):
                fallback_hits += 1
            else:
                failures.append(question)

    print(f"\n=== {label} Evaluation ===")
    print("Answerable retrieval hits:", retrieval_hits, "/ 12")
    print("Expected facts found:", fact_hits, "/ 12")
    print("Unanswerable fallback hits:", fallback_hits, "/ 2")

    print("Failed questions:")
    for question in failures:
        print("-", question)

    return retrieval_hits, fact_hits, fallback_hits


def get_order(order_id):
    conn = sqlite3.connect("data/instamart.db")
    conn.row_factory = sqlite3.Row

    try:
        row = conn.execute(
            """
            SELECT order_id, status, order_amount, delivery_minutes
            FROM orders
            WHERE order_id = ?
            """,
            (order_id,)
        ).fetchone()

        if row is None:
            return {"error": "Order not found"}

        return {
            "order_id": row["order_id"],
            "status": row["status"],
            "order_amount": float(row["order_amount"]),
            "delivery_minutes": (
                float(row["delivery_minutes"])
                if row["delivery_minutes"] is not None
                else None
            )
        }

    finally:
        conn.close()


def search_policy(query):
    return {"results": retrieve(query, k=3)}


def calculate_refund(order_amount, delivery_minutes):
    if delivery_minutes is None:
        return {"refund_inr": 0.0}

    refund = float(order_amount) if delivery_minutes > 45 else 0.0

    return {"refund_inr": round(refund, 2)}


def write_refund_ledger(tool_name, order_id, refund_inr):
    os.makedirs("outputs", exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "order_id": order_id,
        "refund_inr": round(float(refund_inr), 2)
    }

    with open("outputs/refund_ledger.jsonl", "a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")

    return {"refund_inr": round(float(refund_inr), 2)}


def issue_refund(order_id, refund_inr):
    return write_refund_ledger(
        "issue_refund", order_id, refund_inr
    )


def escalate_to_human(order_id, refund_inr):
    return write_refund_ledger(
        "escalate_to_human", order_id, refund_inr
    )

TOOLS_SPEC = [
    {
        "name": "get_order",
        "description": "Retrieve an order's status, amount and delivery time.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "search_policy",
        "description": "Search the policy documents for relevant information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculate_refund",
        "description": "Calculate the refund based on order amount and delivery time.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_amount": {"type": "number"},
                "delivery_minutes": {"type": "number"}
            },
            "required": ["order_amount", "delivery_minutes"]
        }
    },
    {
        "name": "issue_refund",
        "description": "Record an automatically approved refund in the refund ledger.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "refund_inr": {"type": "number"}
            },
            "required": ["order_id", "refund_inr"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Record a refund requiring human approval.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "refund_inr": {"type": "number"}
            },
            "required": ["order_id", "refund_inr"]
        }
    }
]


TOOL_MAP = {
    "get_order": get_order,
    "search_policy": search_policy,
    "calculate_refund": calculate_refund,
    "issue_refund": issue_refund,
    "escalate_to_human": escalate_to_human
}


def _continue_agent(
    run_id,
    scenario_id,
    messages,
    steps,
    tools_executed,
    llm_calls,
    tokens_used,
    iterations,
    max_iterations,
    token_limit,
    time_limit_seconds,
    crash_after_tools=None
):
    checkpoint_path = f"state/{run_id}.json"
    os.makedirs("state", exist_ok=True)

    start_time = time.monotonic()

    def save_checkpoint():
        checkpoint = {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "messages": messages,
            "tokens_used": tokens_used,
            "step_number": len(steps),
            "tools_executed": tools_executed,
            "steps": steps,
            "llm_calls": llm_calls,
            "iterations": iterations
        }

        with open(checkpoint_path, "w", encoding="utf-8") as file:
            json.dump(checkpoint, file, indent=2)

    def fallback(status, reason):
        return {
            "status": status,
            "final_answer": (
                f"{status}: {reason} "
                "The request requires human review."
            ),
            "steps": steps,
            "llm_calls": llm_calls,
            "tokens_used": tokens_used
        }

    while iterations < max_iterations:

        if time.monotonic() - start_time >= time_limit_seconds:
            return fallback(
                "FALLBACK_TIMEOUT",
                "The time limit was reached."
            )

        response = mock_llm.chat(messages, tools=TOOLS_SPEC)

        iterations += 1
        llm_calls += 1
        tokens_used += response.usage.total_tokens

        if tokens_used > token_limit:
            return fallback(
                "FALLBACK_TOKEN_LIMIT",
                "The token limit was exceeded."
            )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls

        if not tool_calls:
            final_answer = assistant_message.content or ""

            return {
                "status": final_answer.split(":", 1)[0],
                "final_answer": final_answer,
                "steps": steps,
                "llm_calls": llm_calls,
                "tokens_used": tokens_used
            }

        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments)
                    }
                }
                for call in tool_calls
            ]
        })

        for call in tool_calls:
            tool_name = call.name
            arguments = call.arguments

            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            if tool_name not in TOOL_MAP:
                observation = {"error": "Unknown tool"}
            else:
                observation = TOOL_MAP[tool_name](**arguments)

            steps.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": observation
            })

            tools_executed.append(tool_name)

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": tool_name,
                "content": json.dumps(observation)
            })

            # Save state immediately after every tool observation.
            save_checkpoint()

            # Simulate a crash only after the checkpoint is saved.
            if (
                crash_after_tools is not None
                and len(tools_executed) == crash_after_tools
            ):
                raise RuntimeError("Simulated agent crash")

    return fallback(
        "FALLBACK_MAX_ITERATIONS",
        "The maximum number of agent iterations was reached."
    )


def run_agent(
    user_message,
    scenario_id,
    max_iterations=6,
    token_limit=6000,
    time_limit_seconds=10,
    run_id=None,
    crash_after_tools=None
):
    run_id = run_id or scenario_id

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AGENT for Instamart customer refunds. "
                "Use the supplied tools to check orders and follow refund rules. "
                "Only completed orders are eligible. "
                "Refunds above INR 1000 require human approval."
            )
        },
        {"role": "user", "content": user_message}
    ]

    return _continue_agent(
        run_id=run_id,
        scenario_id=scenario_id,
        messages=messages,
        steps=[],
        tools_executed=[],
        llm_calls=0,
        tokens_used=0,
        iterations=0,
        max_iterations=max_iterations,
        token_limit=token_limit,
        time_limit_seconds=time_limit_seconds,
        crash_after_tools=crash_after_tools
    )


def resume_agent(
    run_id,
    max_iterations=6,
    token_limit=6000,
    time_limit_seconds=10
):
    checkpoint_path = f"state/{run_id}.json"

    with open(checkpoint_path, "r", encoding="utf-8") as file:
        checkpoint = json.load(file)

    return _continue_agent(
        run_id=run_id,
        scenario_id=checkpoint["scenario_id"],
        messages=checkpoint["messages"],
        steps=checkpoint["steps"],
        tools_executed=checkpoint["tools_executed"],
        llm_calls=checkpoint["llm_calls"],
        tokens_used=checkpoint["tokens_used"],
        iterations=checkpoint["iterations"],
        max_iterations=max_iterations,
        token_limit=token_limit,
        time_limit_seconds=time_limit_seconds
    )


if __name__ == "__main__":

    # Evaluate with 10-word overlap
    normal_chunks = load_policy_documents(overlap=10)

    evaluate_policy(
        normal_chunks,
        "10-word overlap"
    )

    # Evaluate with zero overlap
    zero_overlap_chunks = load_policy_documents(overlap=0)

    evaluate_policy(
        zero_overlap_chunks,
        "Zero overlap"
    )