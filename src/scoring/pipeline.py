from typing import Any


def score_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Placeholder scoring pipeline. Branch feature/scoring-pipeline owns full implementation."""
    for item in posts:
        item.setdefault("rule_score", 0.0)
        item.setdefault("llm_score", 0.0)
        item["final_score"] = round(float(item["rule_score"]) + float(item["llm_score"]), 4)
    return sorted(posts, key=lambda x: x.get("final_score", 0.0), reverse=True)

