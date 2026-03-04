from neo4j import GraphDatabase
import hashlib


def generate_claim_id(claim):
    base = f"{claim.type}|{claim.subject}|{claim.object or ''}|{claim.valid_from}"
    return hashlib.sha256(base.encode()).hexdigest()


class Neo4jGraph:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def insert_artifact(self, tx, artifact_id, subject, sender, timestamp):
        tx.run("""
        MERGE (a:Artifact {artifact_id: $artifact_id})
        SET a.subject = $subject,
            a.sender = $sender,
            a.timestamp = $timestamp
        """,
        artifact_id=artifact_id,
        subject=subject,
        sender=sender,
        timestamp=str(timestamp)
        )

    def insert_entity(self, tx, entity):
        normalized = entity.email if entity.email else entity.name.lower()

        tx.run("""
        MERGE (e:Entity {normalized_name: toLower($normalized_name)})
        ON CREATE SET
            e.name = $name,
            e.type = $type,
            e.email = $email
        """,
        normalized_name=normalized,
        name=entity.name,
        type=entity.type,
        email=entity.email
        )
        
    def insert_claim(self, tx, claim):

        claim_id = generate_claim_id(claim)

        tx.run("""
        MERGE (s:Entity {normalized_name: toLower($subject)})
        ON CREATE SET s.name = $subject

        MERGE (c:Claim {claim_id: $claim_id})

        SET c.type = $type,
            c.subject = $subject,
            c.object = $object,
            c.valid_from = $valid_from,
            c.event_time = $event_time,
            c.confidence = $confidence,
            c.valid_to = $valid_to

        MERGE (s)-[:MADE_CLAIM]->(c)
        """,
        claim_id=claim_id,
        subject=claim.subject,
        type=claim.type,
        object=claim.object,
        valid_from=str(claim.valid_from) if claim.valid_from else None,
        event_time=str(claim.event_time) if claim.event_time else None,
        confidence=claim.confidence,
        valid_to=str(claim.valid_to) if claim.valid_to else None
        )

    def insert_evidence(self, tx, claim, artifact_id, message_id):

        claim_id = generate_claim_id(claim)

        tx.run("""
        MATCH (c:Claim {claim_id: $claim_id})
        MATCH (a:Artifact {artifact_id: $artifact_id})

        CREATE (e:Evidence {
            quote: $quote,
            char_start: $char_start,
            char_end: $char_end,
            message_id: $message_id,
            extracted_at: datetime()
        })

        MERGE (c)-[:SUPPORTED_BY]->(e)
        MERGE (e)-[:FROM_ARTIFACT]->(a)
        """,
        claim_id=claim_id,
        artifact_id=artifact_id,
        message_id=message_id,
        quote=claim.evidence.quote,
        char_start=claim.evidence.char_start,
        char_end=claim.evidence.char_end
        )

    def insert_full(self, extracted_output, artifact_id, subject, sender, timestamp, message_id):

        with self.driver.session() as session:

            session.execute_write(
                self.insert_artifact,
                artifact_id,
                subject,
                sender,
                timestamp
            )

            for entity in extracted_output.entities:
                session.execute_write(self.insert_entity, entity)

            for claim in extracted_output.claims:
                session.execute_write(self.insert_claim, claim)
                session.execute_write(self.insert_evidence, claim, artifact_id, message_id)
