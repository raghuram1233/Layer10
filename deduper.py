from collections import defaultdict


def claim_key(claim):
    return (
        claim.type,
        claim.subject.lower(),
        claim.object.lower() if claim.object else "",
        str(claim.event_time)
    )


def deduplicate_claims(claims):
    grouped = defaultdict(list)

    for claim in claims:
        grouped[claim_key(claim)].append(claim)

    merged = []

    for key, claim_list in grouped.items():
        if len(claim_list) == 1:
            merged.append(claim_list[0])
        else:
            base = claim_list[0]
            base.confidence = max(c.confidence for c in claim_list)
            merged.append(base)

    return merged