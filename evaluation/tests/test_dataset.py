"""
evaluation/tests/test_dataset.py
Schema and sanity checks for evaluation/datasets/agent_tasks.json.
No API calls needed.
"""

import json
from pathlib import Path

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "agent_tasks.json"

VALID_ANSWER_CHECKS = {"exact", "numeric", "contains", "none"}
VALID_TOOL_MATCHES = {"exact", "subset", "none"}
REQUIRED_FIELDS = ("id", "category", "prompt", "expected_tools", "tool_match", "answer_check")


def _load() -> list[dict]:
    with open(DATASET_PATH, encoding="utf-8") as f:
        data: list[dict] = json.load(f)
        return data


def test_dataset_file_exists_and_loads_as_a_list():
    data = _load()
    assert isinstance(data, list)
    assert 15 <= len(data) <= 25


def test_task_ids_are_unique():
    data = _load()
    ids = [t["id"] for t in data]
    assert len(ids) == len(set(ids))


def test_every_task_has_required_fields():
    data = _load()
    for task in data:
        for field_name in REQUIRED_FIELDS:
            assert field_name in task, f"{task.get('id')} is missing '{field_name}'"


def test_answer_check_values_are_valid():
    data = _load()
    for task in data:
        assert task["answer_check"] in VALID_ANSWER_CHECKS, task["id"]


def test_tool_match_values_are_valid():
    data = _load()
    for task in data:
        assert task["tool_match"] in VALID_TOOL_MATCHES, task["id"]


def test_expected_tools_is_always_a_list():
    data = _load()
    for task in data:
        assert isinstance(task["expected_tools"], list), task["id"]


def test_tasks_with_an_answer_check_declare_an_expected_answer():
    data = _load()
    for task in data:
        if task["answer_check"] != "none":
            assert task.get("expected_answer") is not None, task["id"]


def test_numeric_checks_have_a_numeric_expected_answer():
    data = _load()
    for task in data:
        if task["answer_check"] == "numeric":
            float(task["expected_answer"])  # raises if not numeric


def test_categories_cover_the_scenarios_required_by_the_spec():
    data = _load()
    categories = {t["category"] for t in data}
    required = {"calculator", "multi_step", "no_tool", "tool_selection", "edge_case"}
    assert required.issubset(categories)
