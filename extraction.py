import pandas as pd
import hashlib
from normalizer import deduplicate_entities
from models import ExtractedOutput
from prompts import build_extraction_prompt
import requests
import json
from email import policy
from email.parser import Parser
from email.utils import parsedate_to_datetime,parseaddr
import pytz


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral:latest"


def load_emails(csv_path: str):
    df = pd.read_csv(csv_path)
    df.fillna("", inplace=True)

    # Normalize column names
    df.columns = [c.lower() for c in df.columns]

    if "message" in df.columns:
        df["body"] = df["message"]
    elif "content" in df.columns:
        df["body"] = df["content"]

    return df

def normalize_email_timestamp(date_str):
    dt = parsedate_to_datetime(date_str)
    return dt.astimezone(pytz.UTC)

def clean_body(body: str):
    """
    Remove quoted blocks and forwarded sections
    """
    lines = body.split("\n")
    cleaned = []
    for line in lines:
        if line.strip().startswith(">"):
            continue
        if "-----Original Message-----" in line:
            break
        cleaned.append(line)
    return "\n".join(cleaned)


def hash_artifact(text: str):
    return hashlib.sha256(text.encode()).hexdigest()


def call_llm(prompt: str):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "num_predict": 1024,
                "temperature": 0.0,
                "num_thread":12
            }
        }
    )

    if response.status_code != 200:
        print("ERROR STATUS:", response.status_code)
        print("ERROR BODY:", response.text)
        return None

    return response.json()["response"]


def extract_structured(email_row):
    raw_text = email_row["message"]
    subject, sender, date, body = parse_raw_email(raw_text)
    date = str(normalize_email_timestamp(date))
    cleaned_body = str(clean_body(body))
    prompt = build_extraction_prompt(
        subject=subject,
        body=cleaned_body,
        sender=sender,
        timestamp=date,
    )

    print("subject:" + subject)
    print("sender:" + sender)
    print("date:" + date)
    print("body:" + body)
    print("cleaned body:" + cleaned_body)

    print("-------------------------------------------------")

    raw_output = call_llm(prompt)

    print(raw_output)

    if raw_output is None:
        return None, None, None

    try:
        data = json.loads(raw_output)
    except:
        print("Invalid JSON from LLM")
        return None, None, None

    # 🔹 Defensive cleaning + normalization
    cleaned_claims = []

    sender_normalized = sender.lower().strip()
    email_date = date  # already normalized UTC string

    ALLOWED_TYPES = {
        "MeetingPlan",
        "Decision",
        "Intent",
        "Commitment",
        "Ownership",
        "RoleAssignment",
        "FinancialStatement",
        "Misc"
    }

    for claim in data.get("claims", []):

        # Skip invalid types
        if claim.get("type") not in ALLOWED_TYPES:
            continue

        # Drop Misc completely
        if claim.get("type") == "Misc":
            continue

        # Default subject → sender
        if not claim.get("subject"):
            claim["subject"] = sender_normalized
        else:
            if "@" in claim["subject"]:
                claim["subject"] = claim["subject"].lower().strip()
            else:
                claim["subject"] = sender_normalized

        # Default event_time → email timestamp
        if not claim.get("event_time"):
            claim["event_time"] = email_date

        # Default valid_from → event_time
        if not claim.get("valid_from"):
            claim["valid_from"] = claim["event_time"]

        # Require evidence
        if not claim.get("evidence"):
            continue

        # -------------------------------------------------
        # Improve MeetingPlan object selection
        # -------------------------------------------------
        if claim.get("type") == "MeetingPlan":

            obj = claim.get("object")

            # Weak object (just person name)
            if obj and "@" not in obj and len(obj.split()) <= 2:

                quote_original = claim["evidence"]["quote"]
                quote_lower = quote_original.lower()

                if "schedule of" in quote_lower:
                    start = quote_lower.find("schedule of")
                    claim["object"] = quote_original[start:].strip()

                elif "meeting" in quote_lower:
                    claim["object"] = quote_original.strip()

                elif "plan" in quote_lower:
                    claim["object"] = quote_original.strip()

        cleaned_claims.append(claim)

    data["claims"] = cleaned_claims

    try:
        parsed = ExtractedOutput(**data)
        parsed.entities = deduplicate_entities(parsed.entities)
        return parsed, cleaned_body, date
    except Exception as e:
        print("Validation failed after cleaning:", e)
        return None, None, None

def parse_raw_email(raw_text):
    msg = Parser(policy=policy.default).parsestr(raw_text)

    subject = msg["subject"]
    _, sender_email = parseaddr(msg["from"])
    sender = sender_email.lower().strip()
    date = msg["date"]

    if msg.is_multipart():
        body = ""
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body += part.get_content()
    else:
        body = msg.get_content()

    return subject, sender, date, body