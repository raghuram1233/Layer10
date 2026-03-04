def build_extraction_prompt(subject, body, sender, timestamp):

    return f"""
You are a STRICT structured information extraction system.

Your task is to extract high-quality, durable knowledge from an email.

The output will be stored in a long-term memory graph.
Only extract information that represents meaningful organizational knowledge.

------------------------------------------------------------
WHAT TO EXTRACT
------------------------------------------------------------

Extract claims ONLY if they represent:

• A decision being made
• A role being assigned
• An ownership relationship
• A financial statement
• A commitment or promise
• A meeting plan (proposal, scheduling, rescheduling)
• A clearly expressed intent

Do NOT extract:

• Greetings
• Casual conversation
• Login credentials
• Passwords
• Network configuration
• Internal system codes
• Raw metadata
• Contact lists without role change
• Generic statements without actionable meaning

If nothing qualifies, return:
{{"entities": [], "claims": []}}

------------------------------------------------------------
ENTITY RULES
------------------------------------------------------------

Allowed entity types:
Person, Organization, Project, Topic

Only extract entities that are directly involved in a claim.

Do NOT extract entities that are merely mentioned but not part of a claim.

For Person entities, if the person is referred to by multiple names or nicknames,
extract the primary name and include any aliases used in the email.

------------------------------------------------------------
CLAIM STRUCTURE RULES
------------------------------------------------------------

Each claim must clearly define:

• subject → WHO is making or responsible for the claim
• object → WHAT the claim is about (never just a person unless role/ownership)
• value → structured details only when necessary
• event_time → when it happened
• valid_from → when it becomes true
• valid_to → when it stops being true

------------------------------------------------------------
MEETINGPLAN STRICT RULES
------------------------------------------------------------

For MeetingPlan claims:

1. subject MUST be the person proposing or scheduling the meeting.
2. object MUST describe the meeting topic or purpose.
3. NEVER use a person name as object unless the meeting topic is explicitly about that person.
4. If the meeting concerns a document, salary review, business plan, discussion topic, etc.,
   that phrase must be the object.
5. Time expressions (e.g., "Tuesday at 11:45") must go in:
   - event_time (email timestamp)
   - valid_from (actual meeting time if known)
6. If only a time is mentioned and no topic exists,
   then object may describe the meeting itself (e.g., "meeting scheduling").

GOOD MeetingPlan example:
"Let's review the salary structure on Tuesday."
→ subject: sender
→ object: "review of salary structure"
→ valid_from: Tuesday time

BAD MeetingPlan example:
→ object: "John" ❌

------------------------------------------------------------
OBJECT SELECTION RULES (VERY IMPORTANT)
------------------------------------------------------------

The object must represent the semantic focus of the claim.

Ask yourself:
"What is this claim fundamentally about?"

Not:
"Who is mentioned?"

If object is too short (1–2 words) and looks like a name,
expand it using the evidence quote.

Prefer:
• full noun phrases
• document names
• discussion topics
• financial figures
• proposals

------------------------------------------------------------
TIME RULES
------------------------------------------------------------

• Use ISO 8601 format: YYYY-MM-DDTHH:MM:SS
• Remove timezone offsets
• If unknown → null
• valid_from should represent when the claim becomes true
• event_time is the email timestamp unless specified otherwise

------------------------------------------------------------
CONFIDENCE
------------------------------------------------------------

• 0.9–1.0 → explicitly stated
• 0.75–0.85 → clearly implied
• Below 0.6 → do not extract

------------------------------------------------------------
EVIDENCE RULES (CRITICAL)
------------------------------------------------------------

• evidence.quote MUST be an EXACT substring from EMAIL BODY
• char_start and char_end must match exact character positions
• Do NOT modify punctuation
• If exact span cannot be located → DO NOT extract claim

------------------------------------------------------------
EMAIL METADATA
------------------------------------------------------------

Sender: {sender}
Timestamp: {timestamp}
Subject: {subject}

------------------------------------------------------------
EMAIL BODY
------------------------------------------------------------

{body}

------------------------------------------------------------
REQUIRED OUTPUT FORMAT
------------------------------------------------------------

Return ONLY valid JSON:

{{
  "entities": [
    {{
      "type": "Person|Organization|Project|Topic",
      "name": "string",
      "email": "string or null",
      "aliases": ["string", "string"] or []
    }}
  ],
  "claims": [
    {{
      "type": "RoleAssignment|Decision|Intent|Commitment|Ownership|FinancialStatement|MeetingPlan",
      "subject": "string",
      "object": "string or null",
      "value": {{}},
      "event_time": "ISO string or null",
      "valid_from": "ISO string or null",
      "valid_to": "ISO string or null",
      "confidence": 0.0,
      "evidence": {{
        "quote": "exact substring from EMAIL BODY",
        "char_start": 0,
        "char_end": 0
      }}
    }}
  ]
}}

NO markdown.
NO explanation.
NO extra text.
ONLY JSON.
"""