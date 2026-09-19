from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import requests


def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def search(base_url: str, search_path: str, question: str) -> tuple[float, dict[str, Any]]:
    started = time.perf_counter()
    response = requests.post(
        f"{base_url.rstrip('/')}/{search_path.strip('/')}/",
        json={"query": question},
        timeout=120,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.raise_for_status()
    return elapsed_ms, response.json()


def run_performance(
    base_url: str,
    search_path: str,
    cases: list[dict[str, Any]],
    concurrency: int,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(search, base_url, search_path, case["question"])
            for case in cases
        ]
        results = [future.result() for future in futures]
    wall_seconds = time.perf_counter() - started
    latencies = [elapsed_ms for elapsed_ms, _ in results]
    report = {
        "requests": float(len(results)),
        "concurrency": float(concurrency),
        "wall_time_seconds": round(wall_seconds, 4),
        "throughput_requests_per_second": round(
            len(results) / wall_seconds if wall_seconds else 0, 4
        ),
        "latency_ms_min": round(min(latencies), 2),
        "latency_ms_mean": round(statistics.mean(latencies), 2),
        "latency_ms_p50": round(statistics.median(latencies), 2),
        "latency_ms_p95": round(
            sorted(latencies)[max(0, math.ceil(len(latencies) * 0.95) - 1)], 2
        ),
        "latency_ms_max": round(max(latencies), 2),
    }
    rows = []
    for case, (elapsed_ms, payload) in zip(cases, results):
        rows.append(
            {
                "question": case["question"],
                "latency_ms": round(elapsed_ms, 2),
                "answer": case.get("answer", ""),
                "reference": case.get("reference", ""),
                "reference_contexts": case.get("reference_contexts", []),
                "retrieved_contexts": [
                    result["content"] for result in payload.get("results", [])
                ],
                "response": payload,
            }
        )
    return rows, report


def score_with_ragas(rows: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        from ragas import EvaluationDataset, SingleTurnSample, evaluate
        from ragas.metrics import ContextPrecision, ContextRecall
    except ImportError as error:
        raise RuntimeError(
            "Ragas is optional. Install it with: "
            "pip install -r requirements-evaluation.txt"
        ) from error

    samples = [
        SingleTurnSample(
            user_input=row["question"],
            response=row["answer"],
            retrieved_contexts=row["retrieved_contexts"],
            reference=row["reference"],
            reference_contexts=row["reference_contexts"],
        )
        for row in rows
    ]
    result = evaluate(
        EvaluationDataset(samples=samples),
        metrics=[ContextPrecision(), ContextRecall()],
    )
    return result.to_pandas().to_dict(orient="records")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--search-path", default="api/v1/search/")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("evaluation/report.json"))
    parser.add_argument("--skip-ragas", action="store_true")
    args = parser.parse_args()

    cases = load_cases(args.dataset)
    rows, performance = run_performance(
        args.base_url, args.search_path, cases, args.concurrency
    )
    report: dict[str, Any] = {
        "base_url": args.base_url,
        "performance": performance,
        "requests": rows,
    }
    if not args.skip_ragas:
        report["ragas"] = score_with_ragas(rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
