import json
from qa_pipeline import MemoryQA


def print_results(result):

    print("\n===================================")
    print("QUESTION:", result["question"])
    print("KEYWORDS:", ", ".join(result["keywords"]))
    print("===================================\n")

    matches = result.get("top_matches", [])[:3]

    if not matches:
        print("No relevant matches found.\n")
        return

    for i, claim in enumerate(matches, start=1):

        print(f"Match #{i}")
        print("-----------------------------------")

        print("Claim Type      :", claim.get("type"))
        print("Subject         :", claim.get("subject"))
        print("Object          :", claim.get("object"))
        print("Confidence      :", claim.get("confidence"))
        print("Relevance Score :", claim.get("score"))

        print("\nSource Email")
        print("  Sender  :", claim.get("artifact_sender"))
        print("  Subject :", claim.get("artifact_subject"))

        print("\nEvidence")
        print(f"  \"{claim.get('evidence')}\"")

        print("\n")


def main():

    qa = MemoryQA("bolt://localhost:7687", "neo4j", "asdfghjkl")

    try:

        while True:

            question = input("\nAsk a question (type 'exit' to quit): ")

            if question.lower() == "exit":
                break

            result = qa.answer(question)

            print_results(result)

    finally:
        qa.close()


if __name__ == "__main__":
    main()