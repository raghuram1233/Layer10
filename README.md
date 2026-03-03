# 📧 Email Knowledge Extraction & Graph Memory

This project ingests raw email data, extracts structured “claims” and entities using an LLM, normalises and de‑duplicates the results, and persists everything in a Neo4j knowledge graph. A simple QA layer lets you query the accumulated memory by keywords.

---

## 🔍 What it does

1. **Load** a CSV of emails (`sample_5.csv`, `emails.csv`, etc.).
2. **Parse** the raw MIME text; clean quoted text and forwarded sections.
3. **Call an LLM** (via an Ollama local server) to extract:
   - entities (`Person`, `Organization`, …)
   - claims (`Decision`, `RoleAssignment`, `MeetingPlan`, …)
   - evidence spans with offsets.
4. **Normalise / verify** claims and entity data; deduplicate.
5. **Hash** each email body into an artifact ID.
6. **Persist** artifacts, entities, claims and evidence into Neo4j.
7. **Resume-safe** processing – progress tracked in `progress.json`.
8. **Query** the graph with simple keyword searches or run the QA pipeline.

---

## ⚙️ Requirements

- Python 3.11+
- Neo4j (bolt://localhost:7687 by default)
- [Ollama](https://ollama.com) running locally with a model (default `mistral:latest`)
- `pip` packages listed in `requirements.txt` (see below)

```bash
pip install pandas neo4j requests pydantic pytz
```

> ⚠️ There’s no `requirements.txt` in the repo; you can generate one from the imports above.

---

## 🚀 Getting started

1. **Start Neo4j** and create a user/password (defaults in code: `neo4j`/`asdfghjkl`).
2. **Launch Ollama** with your chosen model.
3. Populate `sample_5.csv` (or your own) with email data; columns should include
   `message`/`content` containing full RFC‑822 text.

4. Run the ingestion script:

```bash
python main.py
```

Progress is stored in `progress.json` so you can safely stop/restart.

---

## 🧱 Core modules

| File                 | Purpose |
|----------------------|---------|
| `extraction.py`      | Load emails, clean body, call LLM and validate output |
| `prompts.py`         | LLM prompt template enforcing strict extraction rules |
| `normalizer.py`      | String normalization, deduplication, evidence fixing |
| `models.py`          | Pydantic models for entities/claims/evidence |
| `graph_builder.py`   | Neo4j wrapper for inserting artifacts, entities, claims |
| `deduper.py`         | Utility to merge duplicate claims |
| `qa_pipeline.py`     | Keyword-based search & simple QA over the graph |
| `query.py`           | Example usage of `MemoryQA` class |

---

## 🗃️ Data files

- `emails.csv`, `sample_5.csv` – sample input data.
- `progress.json` – stores the last processed row index.
- `operations.ipynb` – notebook for exploratory work.

---

## 🧪 Example query

```python
from query import qa
qa.answer("business meeting")
```

Returns matching artifacts, entities and claims from the Neo4j graph.

---

## 📝 Notes & tips

- Adjust `CSV_PATH`, `PROGRESS_FILE` and database credentials in `main.py`.
- If the LLM returns invalid JSON, the row is skipped with an error message.
- The prompt enforces strict extraction rules – tweak `prompts.py` for
  custom domains.
- Extend the QA layer or integrate a frontend as needed.

---

Feel free to fork, adapt, or extend—this repo is a starting point for building
a long‑term memory system from unstructured email data.
