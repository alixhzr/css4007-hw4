import os
import json
import pathlib

from strategies import run_s1, run_s2, run_s3

OUTPUTS_DIR = pathlib.Path("outputs")
OUTPUTS_DIR.mkdir(exist_ok=True)

def load_corpus():
    docs = []
    corpus_path = pathlib.Path("data/corpus.jsonl")
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                docs.append(f"[{d.get('id')}]: {d.get('title')}\n{d.get('text')}")
    return "\n\n".join(docs)

def load_questions():
    q_path = pathlib.Path("data/questions.json")
    with open(q_path, "r", encoding="utf-8") as f:
        return json.load(f)

def safe_usage(u):
    if hasattr(u, "model_dump"):
        return u.model_dump()
    elif hasattr(u, "dict"):
        return u.dict()
    return dict(u) if u else {}

def main():
    print("Loading data...")
    documents_text = load_corpus()
    questions = load_questions()
    
    print(f"Loaded {len(questions)} questions. Running strategies...")
    
    # Можете для теста запустить сначала на первых 2 вопросах:
    # for q in questions[:2]:
    for q in questions:
        qid = q["id"]
        q_text = q["question"]
        print(f"Processing {qid}...")
        
        # S1
        ans_s1, usage_s1, time_s1 = run_s1(q_text, documents_text)
        
        # S2
        answers_s2, usage_s2, time_s2 = run_s2(q_text, documents_text, k=5)
        ans_s2 = max(set(answers_s2), key=answers_s2.count)
        
        # S3
        ans_s3, usage_s3, time_s3, log_steps_s3 = run_s3(q_text)
        
        # Сохранение логов в outputs/
        log_data = {
            "question_id": qid,
            "question": q_text,
            "s1": {"answer": ans_s1, "usage": safe_usage(usage_s1), "time": time_s1},
            "s2": {"answers": answers_s2, "chosen": ans_s2, "usage": safe_usage(usage_s2), "time": time_s2},
            "s3": {"answer": ans_s3, "usage": safe_usage(usage_s3), "time": time_s3, "steps": log_steps_s3}
        }
        
        with open(OUTPUTS_DIR / f"{qid}.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

    print("All runs completed! Logs saved to outputs/")

if __name__ == "__main__":
    main()