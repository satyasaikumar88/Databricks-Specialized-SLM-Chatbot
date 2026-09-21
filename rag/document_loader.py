from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_documents(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f'Document file not found: {file_path}')

    with file_path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError('Expected a JSON list of documentation objects.')
    return data
