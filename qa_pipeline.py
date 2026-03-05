from neo4j import GraphDatabase
import re


STOPWORDS = {
    "who","what","when","where","why",
    "how","is","was","the","a","an",
    "did","to","of","in","on"
}


def extract_keywords(question):
    tokens = re.findall(r"\b\w+\b", question.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


class MemoryQA:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))


    def close(self):
        self.driver.close()


    def search_claims(self, keywords):

        query = """
        MATCH (c:Claim)-[:SUPPORTED_BY]->(ev:Evidence)-[:FROM_ARTIFACT]->(a:Artifact)

        WITH c, ev, a,
        (
            CASE WHEN ANY(k IN $keywords WHERE toLower(c.subject) CONTAINS k) THEN 2 ELSE 0 END +
            CASE WHEN ANY(k IN $keywords WHERE toLower(c.object) CONTAINS k) THEN 3 ELSE 0 END +
            CASE WHEN ANY(k IN $keywords WHERE toLower(ev.quote) CONTAINS k) THEN 2 ELSE 0 END +
            CASE WHEN ANY(k IN $keywords WHERE toLower(a.subject) CONTAINS k) THEN 1 ELSE 0 END
        ) AS score

        WHERE score > 0

        RETURN c, ev, a, score
        ORDER BY score DESC
        LIMIT 3
        """

        with self.driver.session() as session:

            results = session.run(query, keywords=keywords)

            matches = []

            for r in results:

                claim = r["c"]
                evidence = r["ev"]
                artifact = r["a"]

                matches.append({
                    "type": claim["type"],
                    "subject": claim["subject"],
                    "object": claim.get("object"),
                    "event_time": claim.get("event_time"),
                    "confidence": claim.get("confidence"),
                    "score": r["score"],
                    "evidence": evidence["quote"],
                    "artifact_subject": artifact.get("subject"),
                    "artifact_sender": artifact.get("sender")
                })

            return matches


    def answer(self, question):

        keywords = extract_keywords(question)

        claims = self.search_claims(keywords)

        return {
            "question": question,
            "keywords": keywords,
            "top_matches": claims
        }