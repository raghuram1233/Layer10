from qa_pipeline import MemoryQA

qa = MemoryQA("bolt://localhost:7687", "neo4j", "asdfghjkl")

result = qa.answer("business meeting ")

print(result)

qa.close()