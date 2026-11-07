
import json
import os
import pandas as pd
import policy_rag
import mock_llm

os.makedirs("outputs", exist_ok=True)
os.makedirs("state", exist_ok=True)

# Start with a clean refund ledger.
open("outputs/refund_ledger.jsonl", "w", encoding="utf-8").close()

scenarios = pd.read_csv("data/raw/agent_scenarios.csv")

with open("outputs/agent_runs.jsonl", "w", encoding="utf-8") as output_file:

    for _, scenario in scenarios.iterrows():
        scenario_id = scenario["scenario_id"]

        mock_llm.reset()

        result = policy_rag.run_agent(
            user_message=scenario["message"],
            scenario_id=scenario_id,
            run_id=f"final_{scenario_id}"
        )

        record = {
            "scenario_id": scenario_id,
            "status": result["status"],
            "final_answer": result["final_answer"],
            "llm_calls": result["llm_calls"],
            "tokens_used": result["tokens_used"],
            "steps": [
                {
                    "tool_name": step["tool_name"],
                    "arguments": step["arguments"],
                    "observation": step["observation"]
                }
                for step in result["steps"]
            ]
        }

        output_file.write(json.dumps(record) + "\n")

        print(
            scenario_id,
            "| Status:", result["status"],
            "| Calls:", result["llm_calls"],
            "| Tokens:", result["tokens_used"]
        )

print("\nFinal agent outputs generated successfully.")
