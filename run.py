"""Run the Vision One Million scorecard pipeline."""

from __future__ import annotations

import json
import sys

from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator import build_graph
from schema.state import Initiative
from schema.graph import PipelineState

# ── Colors ───────────────────────────────────────────────────────────────────
G = "\033[32m"; R = "\033[31m"; Y = "\033[33m"; B = "\033[34m"; C = "\033[36m"
DIM = "\033[2m"; BOLD = "\033[1m"; RESET = "\033[0m"


def load_initiatives(path: str = "output.json") -> list[Initiative]:
    with open(path) as f:
        data = json.load(f)

    initiatives = []
    for category in data["scorecard"]["categories"]:
        for init in category["initiatives"]:
            initiatives.append(Initiative(
                id=init["id"],
                category=init["category"],
                name=init["name"],
                metric_label=init["metric"]["value"],
                target_value=init["target"]["value"],
            ))
    return initiatives


def run_single(initiative: Initiative) -> PipelineState:
    graph = build_graph()
    initial_state: PipelineState = {
        "initiative": initiative.model_dump(),
        "sources": [],
        "extracted": [],
        "is_valid": False,
        "validation_errors": [],
        "retry_count": 0,
        "status": "NO_ASSESSMENT",
        "status_reasoning": "",
        "error": "",
    }
    return graph.invoke(initial_state)


def run_all() -> dict:
    initiatives = load_initiatives()

    print(f"\n{BOLD}Vision One Million Scorecard Pipeline{RESET}")
    print(f"{DIM}Processing {len(initiatives)} initiatives...{RESET}\n")
    print("=" * 60)

    results = []
    for i, init in enumerate(initiatives):
        print(f"\n{BOLD}[{i+1}/{len(initiatives)}]{RESET} {C}{init.name}{RESET}")
        print("-" * 60)
        try:
            result = run_single(init)
            results.append(result)
        except Exception as e:
            print(f"  {R}PIPELINE ERROR: {e}{RESET}")
            results.append({
                "initiative": init.model_dump(),
                "status": "NO_ASSESSMENT",
                "status_reasoning": f"Pipeline error: {e}",
            })
        print("=" * 60)

    scorecard = build_scorecard(results)
    return scorecard


def build_scorecard(results: list[PipelineState]) -> dict:
    categories: dict[str, dict] = {}

    for result in results:
        init = result["initiative"]
        cat = init["category"]

        if cat not in categories:
            cat_id = init["id"].rsplit("-", 1)[0]
            categories[cat] = {"id": cat_id, "name": cat, "status": "NO_ASSESSMENT", "initiatives": []}

        categories[cat]["initiatives"].append({
            "id": init["id"],
            "category": cat,
            "name": init["name"],
            "metric": {"label": "Metric", "value": init["metric_label"]},
            "target": {"label": "Target", "value": init["target_value"]},
            "status": result.get("status", "NO_ASSESSMENT"),
            "status_reasoning": result.get("status_reasoning", ""),
        })

    for cat in categories.values():
        statuses = [i["status"] for i in cat["initiatives"]]
        cat["status"] = max(set(statuses), key=statuses.count)

    return {
        "scorecard": {
            "title": "Vision 1 Million Scorecard",
            "organization": "BestWR",
            "version": "auto",
            "categories": list(categories.values()),
        }
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        target_id = sys.argv[2] if len(sys.argv) > 2 else "housing-4"
        initiatives = load_initiatives()
        init = next((i for i in initiatives if i.id == target_id), None)
        if not init:
            print(f"Initiative {target_id} not found")
            sys.exit(1)
        print(f"\n{BOLD}Running pipeline for:{RESET} {C}{init.name}{RESET}\n")
        result = run_single(init)
        print(f"\n{'=' * 60}")
        print(json.dumps(result, indent=2, default=str))
    else:
        scorecard = run_all()
        with open("scorecard_output.json", "w") as f:
            json.dump(scorecard, f, indent=2, default=str)
        print(f"\n{G}{BOLD}Scorecard written to scorecard_output.json{RESET}")
