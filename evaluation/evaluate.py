from __future__ import annotations

import json
from pathlib import Path


def run_evaluation():
    dataset = Path('data/databricks_qa.jsonl')
    if not dataset.exists():
        raise FileNotFoundError('Dataset file was not found. Run the dataset builder first.')

    rows = []
    with dataset.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    evaluation = {
        'total_questions': len(rows),
        'categories': {},
        'metrics': {
            'base_slm': {'correctness': 'not run', 'relevance': 'not run', 'grounding': 'not run'},
            'fine_tuned_slm': {'correctness': 'not run', 'relevance': 'not run', 'grounding': 'not run'},
            'fine_tuned_slm_rag': {'correctness': 'not run', 'relevance': 'not run', 'grounding': 'not run'},
        },
    }

    for row in rows:
        cat = row.get('category', 'general')
        evaluation['categories'][cat] = evaluation['categories'].get(cat, 0) + 1

    output_path = Path('evaluation/results.json')
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(json.dumps(evaluation, indent=2), encoding='utf-8')
    print(f'Evaluation scaffold written to {output_path}')


if __name__ == '__main__':
    run_evaluation()
