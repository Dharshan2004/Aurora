import json
from backend.rag.vector_store import get_vectorstore

def retrieve(query: str, k: int = 5):
    vs = get_vectorstore()
    return vs.similarity_search(query, k=k)

# run: python -c "from tests.quick_retrieval_eval import evaluate_retrieval; evaluate_retrieval()"
def evaluate_retrieval():
    test_cases = json.load(open("tests/eval_examples.json"))
    pass_count = 0
    for case in test_cases:
        docs = retrieve(case["q"])
        blob = " ".join(d.page_content for d in docs)
        if all(s.lower() in blob.lower() for s in case["must_contain"]):
            pass_count += 1
    print(f"Passed {pass_count} out of {len(test_cases)} cases")