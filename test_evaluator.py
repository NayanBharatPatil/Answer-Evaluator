"""Offline tests for the non-LLM logic. Run: python test_evaluator.py"""
from evaluator import _extract_json, compute_marks

assert compute_marks({"content_accuracy": 50, "completeness": 30, "clarity": 20}, 10)[0] == 10
assert compute_marks({"content_accuracy": 999, "completeness": -5, "clarity": "x"}, 10)[0] == 5  # clamped
assert compute_marks({"content_accuracy": 33, "completeness": 20, "clarity": 10}, 5)[0] == 3.0   # 63% of 5 -> 3.0
assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}
assert _extract_json('Here you go: {"a": 2} thanks') == {"a": 2}
print("All tests passed")
