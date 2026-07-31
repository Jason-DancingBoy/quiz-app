import json
import os
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "ragas_output"


def _ensure_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _get_commit_hash() -> str:
    """获取当前 git commit hash，失败返回 'unknown'"""
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def write_latest_json(results: dict):
    """将完整评估结果写入 ragas_results_latest.json（覆盖写入）。"""
    _ensure_dir()
    path = OUTPUT_DIR / "ragas_results_latest.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def write_history(results: dict):
    """将 results 追加写入 ragas_results_history.jsonl（每行一个完整 JSON，追加模式）。"""
    _ensure_dir()
    path = OUTPUT_DIR / "ragas_results_history.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(results, ensure_ascii=False) + "\n")


def write_report(results: dict) -> str:
    """生成人类可读的文本报告，写入 ragas_report.txt，同时返回字符串。"""
    _ensure_dir()

    lines = []
    lines.append("=" * 40)
    lines.append("RAGAS 评估报告")
    lines.append("=" * 40)

    samples_count = len(results.get("samples", []))
    errors_count = len(results.get("errors", []))
    commit = results.get("commit", _get_commit_hash())
    timestamp = results.get("timestamp", datetime.now(timezone.utc).isoformat())

    lines.append(f"Commit: {commit}")
    lines.append(f"Timestamp: {timestamp}")
    lines.append(f"Samples: {samples_count}")
    lines.append(f"Errors: {errors_count}")
    lines.append("")

    # --- 综合指标 ---
    aggregate = results.get("aggregate", {})
    lines.append("--- 综合指标 ---")
    metric_names = {
        "faithfulness": "Faithfulness",
        "format_compliance": "Format Compliance",
        "question_quality": "Question Quality",
    }
    for key, label in metric_names.items():
        if key not in aggregate:
            continue
        val = aggregate[key]
        if key == "format_compliance":
            rate = val.get("rate", 0)
            lines.append(f"{label:24s}{rate * 100:.1f}%")
        elif key == "question_quality":
            mean = val.get("mean", 0)
            std = val.get("std", 0)
            lines.append(f"{label:24s}{mean} ± {std}")
        else:
            mean = val.get("mean", 0)
            std = val.get("std", 0)
            lines.append(f"{label:24s}{mean} ± {std}")
    lines.append("")

    # --- 按难度 ---
    by_difficulty = results.get("by_difficulty", {})
    if by_difficulty:
        lines.append("--- 按难度 ---")
        for diff in ("easy", "medium", "hard"):
            if diff not in by_difficulty:
                continue
            lines.append(f"{diff.capitalize()}:")
            sub = by_difficulty[diff]
            for sub_key, sub_label in metric_names.items():
                if sub_key not in sub:
                    continue
                val = sub[sub_key]
                if sub_key == "format_compliance":
                    rate = val.get("rate", 0)
                    lines.append(f"  {sub_label:22s}{rate * 100:.1f}%")
                elif sub_key == "question_quality":
                    lines.append(f"  {sub_label:22s}{val.get('mean', 0)} ± {val.get('std', 0)}")
                else:
                    lines.append(f"  {sub_label:22s}{val.get('mean', 0)} ± {val.get('std', 0)}")
            lines.append("")

    # --- 按文档长度 ---
    by_doc_length = results.get("by_doc_length", {})
    if by_doc_length:
        lines.append("--- 按文档长度 ---")
        length_labels = {
            "short": "Short (<6000 chars)",
            "medium_len": "Medium (6000-15000 chars)",
            "long": "Long (>15000 chars)",
        }
        for key, label in length_labels.items():
            if key not in by_doc_length:
                continue
            lines.append(f"{label}:")
            sub = by_doc_length[key]
            for sub_key, sub_label in metric_names.items():
                if sub_key not in sub:
                    continue
                val = sub[sub_key]
                if sub_key == "format_compliance":
                    rate = val.get("rate", 0)
                    lines.append(f"  {sub_label:22s}{rate * 100:.1f}%")
                elif sub_key == "question_quality":
                    lines.append(f"  {sub_label:22s}{val.get('mean', 0)} ± {val.get('std', 0)}")
                else:
                    lines.append(f"  {sub_label:22s}{val.get('mean', 0)} ± {val.get('std', 0)}")
            lines.append("")

    report = "\n".join(lines)

    path = OUTPUT_DIR / "ragas_report.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    return report
