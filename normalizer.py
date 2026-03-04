import re
from email.utils import parsedate_to_datetime
import pytz
from typing import List
from models import Entity

def normalize_string(s: str):
    return s.strip().lower() if s else None

def normalize_person(name, email):
    if email:
        return email.lower()
    return name.lower().replace(" ", ".")

def deduplicate_entities(entities: List[Entity]) -> List[Entity]:

    email_map = {}
    name_map = {}

    for entity in entities:

        normalized_name = normalize_string(entity.name)
        normalized_email = normalize_string(entity.email) #type:ignore

        if normalized_email:
            if normalized_email not in email_map:
                email_map[normalized_email] = entity
            else:
                # Prefer entity that has richer data
                existing = email_map[normalized_email]

                # Prefer entity with proper capitalization name
                if existing.name.islower() and not entity.name.islower():
                    email_map[normalized_email] = entity

        else:
            if normalized_name not in name_map:
                name_map[normalized_name] = entity
            else:
                existing = name_map[normalized_name]

                if entity.email and not existing.email:
                    name_map[normalized_name] = entity

    deduped = list(email_map.values())

    for name, entity in name_map.items():

        if entity.email:
            continue

        if any(normalize_string(e.name) == name for e in deduped):
            continue

        deduped.append(entity)

    return deduped

def normalize_email(email: str):
    return email.strip().lower()


def normalize_name(name: str):
    return re.sub(r"\s+", " ", name.strip().lower())


def normalize_email_timestamp(date_str):
    dt = parsedate_to_datetime(date_str)
    return dt.astimezone(pytz.UTC)


def verify_and_fix_evidence(body: str, claim):
    quote = claim.evidence.quote

    try:
        if body[claim.evidence.char_start:claim.evidence.char_end] == quote:
            return True
    except:
        pass

    idx = body.find(quote)
    if idx != -1:
        claim.evidence.char_start = idx
        claim.evidence.char_end = idx + len(quote)
        return True

    idx = body.find(quote.strip())
    if idx != -1:
        claim.evidence.quote = quote.strip()
        claim.evidence.char_start = idx
        claim.evidence.char_end = idx + len(quote.strip())
        return True

    return False