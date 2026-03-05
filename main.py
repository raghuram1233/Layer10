import os
import json
from extraction import load_emails, extract_structured, hash_artifact
from graph_builder import Neo4jGraph
from normalizer import verify_and_fix_evidence

CSV_PATH = "sample_5.csv"
PROGRESS_FILE = "progress.json"

graph = Neo4jGraph("neo4j://127.0.0.1:7687", "neo4j", "asdfghjkl")
df = load_emails(CSV_PATH)

if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        progress_data = json.load(f)
        start_index = progress_data.get("last_index", 0)
else:
    start_index = 0

print(f"Resuming from row index: {start_index}")

for idx in range(start_index, len(df)):

    row = df.iloc[idx]

    try:
        result, cleaned_body, timestamp_utc ,Sender = extract_structured(row)

        if not result:
            with open(PROGRESS_FILE, "w") as f:
                json.dump({"last_index": idx + 1}, f)
            continue

        artifact_id = hash_artifact(cleaned_body)  #type:ignore
        message_id = row.get("message-id", "unknown")

        valid_claims = []
        for claim in result.claims:
            if verify_and_fix_evidence(cleaned_body, claim):        #type:ignore
                valid_claims.append(claim)

        result.claims = valid_claims

        graph.insert_full(
            result,
            artifact_id,
            row.get("subject", ""),
            Sender,
            timestamp_utc,
            message_id
        )

        with open(PROGRESS_FILE, "w") as f:
            json.dump({"last_index": idx + 1}, f)

        print(f"Processed row {idx}")

    except Exception as e:
        print(f"Error at row {idx}: {e}")
        print("Stopping safely. Resume will continue from this row.")
        break

graph.close()
print("Processing complete.")