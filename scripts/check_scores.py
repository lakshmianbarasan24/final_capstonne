import sys
sys.path.insert(0, ".")
import json
from agents.coordinator_agent import CoordinatorAgent
from evaluation.deepeval_runner import evaluate_task_completion

with open('data/golden_dataset_v1.json', 'r', encoding='utf-8') as f:
    samples = json.load(f)['samples']

coord = CoordinatorAgent()
for s in samples:
    if not s['is_restricted']:
        res = coord.review_file(s['filename'])
        score = evaluate_task_completion(res['findings'], s['expected_findings'], s['filename'])
        print(f"{s['id']} ({s['category']}): score={score}, act={len(res['findings'])}, exp={len(s['expected_findings'])}")
        if score < 0.8:
            print("   ACT:", res['findings'])
            print("   EXP:", s['expected_findings'])
