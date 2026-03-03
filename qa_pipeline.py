from neo4j import GraphDatabase
import re


STOPWORDS = {
    "who", "what", "when", "where", "why",
    "how", "is", "was", "the", "a", "an",
    "did", "to", "of", "in", "on"
}


def extract_keywords(question):
    tokens = re.findall(r"\b\w+\b", question.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


class MemoryQA:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # -----------------------------
    # ARTIFACT SEARCH
    # -----------------------------
    def search_artifacts(self, keywords):

        if not keywords:
            return []

        with self.driver.session() as session:

            query = """
            MATCH (a:Artifact)<-[:FROM_ARTIFACT]-(ev:Evidence)

            WITH a, collect(ev) AS evidence

            WITH a,
                [kw IN $keywords WHERE
                    (a.subject IS NOT NULL AND toLower(a.subject) CONTAINS kw) OR
                    (a.sender IS NOT NULL AND toLower(a.sender) CONTAINS kw) OR
                    ANY(ev IN evidence WHERE toLower(ev.quote) CONTAINS kw)
                ] AS matched_keywords

            WITH a, size(matched_keywords) AS keyword_matches
            WHERE keyword_matches > 0

            RETURN a, keyword_matches
            ORDER BY keyword_matches DESC
            LIMIT 20
            """

            records = session.run(query, keywords=keywords)

            results = []

            for record in records:
                a = record["a"]

                results.append({
                    "artifact_id": a["artifact_id"],
                    "subject": a.get("subject"),
                    "sender": a.get("sender"),
                    "timestamp": a.get("timestamp"),
                    "keyword_matches": record["keyword_matches"]
                })

            return results

    # -----------------------------
    # ENTITY SEARCH
    # -----------------------------
    def search_entities(self, keywords):

        if not keywords:
            return []

        with self.driver.session() as session:

            query = """
            MATCH (e:Entity)

            WITH e,
                [kw IN $keywords WHERE
                    (e.name IS NOT NULL AND toLower(e.name) CONTAINS kw) OR
                    (e.normalized_name IS NOT NULL AND toLower(e.normalized_name) CONTAINS kw) OR
                    (e.email IS NOT NULL AND toLower(e.email) CONTAINS kw)
                ] AS matched_keywords

            WITH e, size(matched_keywords) AS keyword_matches
            WHERE keyword_matches > 0

            RETURN e, keyword_matches
            ORDER BY keyword_matches DESC
            LIMIT 20
            """

            records = session.run(query, keywords=keywords)

            results = []

            for record in records:
                e = record["e"]

                results.append({
                    "name": e.get("name"),
                    "type": e.get("type"),
                    "email": e.get("email"),
                    "keyword_matches": record["keyword_matches"]
                })

            return results

    # -----------------------------
    # CLAIM + EVIDENCE SEARCH
    # -----------------------------
    def search_claims(self, keywords):

        if not keywords:
            return []
        with self.driver.session() as session:

            query = """
            MATCH (c:Claim)-[:SUPPORTED_BY]->(ev:Evidence)-[:FROM_ARTIFACT]->(a:Artifact)

            WITH c, collect(ev) AS evidence, a

            WITH c, evidence,
                [kw IN $keywords WHERE
                    toLower(c.subject) CONTAINS kw OR
                    (c.object IS NOT NULL AND toLower(c.object) CONTAINS kw) OR
                    ANY(ev IN evidence WHERE toLower(ev.quote) CONTAINS kw) OR
                    (a.subject IS NOT NULL AND toLower(a.subject) CONTAINS kw)
                ] AS matched_keywords

            WITH c, evidence, size(matched_keywords) AS keyword_matches
            WHERE keyword_matches > 0

            RETURN c, evidence, keyword_matches
            ORDER BY keyword_matches DESC
            """

            records = session.run(query, keywords=keywords)
            print(records)
            results = []

            for record in records:
                c = record["c"]
                evidence_nodes = record["evidence"]
                keyword_matches = record["keyword_matches"]

                results.append({
                    "type": c["type"],
                    "subject": c["subject"],
                    "object": c.get("object"),
                    "event_time": c.get("event_time"),
                    "confidence": c.get("confidence") or 0.0,
                    "keyword_matches": keyword_matches,
                    "evidence": [
                        {
                            "quote": ev["quote"],
                            "message_id": ev["message_id"]
                        }
                        for ev in evidence_nodes
                    ]
                })

            return results

    def answer(self, question):

        keywords = extract_keywords(question)

        claims = self.search_claims(keywords)
        artifacts = self.search_artifacts(keywords)
        entities = self.search_entities(keywords)

        return {
            "question": question,
            "keywords": keywords,
            "entities": entities,
            "claims": claims,
            "artifacts": artifacts
        }