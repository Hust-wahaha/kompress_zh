"""
把 P2 池审核通过的条目合并入 baseline，生成新的联合 labeled_pairs 文件。

用法：
python scripts/merge_p2_into_baseline.py `
    --queue-file   data/interim/review_queue_yyc_sessions_v1.jsonl `
    --audit-file   data/interim/review_audit_p2_yyc_sessions_v1.jsonl `
    --pairs-file   data/raw/labeled_pairs_yyc_sessions_v1.jsonl `
    --baseline-file data/raw/labeled_pairs_pilot_v6_targeted400_p2_audited_merge.jsonl `
    --p2-out       data/raw/labeled_pairs_yyc_sessions_v1_p2_audited_merge.jsonl `
    --combined-out data/raw/labeled_pairs_combined_v7.jsonl

"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-file",    type=Path, required=True)
    parser.add_argument("--audit-file",    type=Path, required=True)
    parser.add_argument("--pairs-file",    type=Path, required=True)
    parser.add_argument("--baseline-file", type=Path, required=True)
    parser.add_argument("--p2-out",        type=Path, required=True)
    parser.add_argument("--combined-out",  type=Path, required=True)
    args = parser.parse_args()

    # 1. 从 review_queue 取 P2 sample_id 集合
    queue_rows = read_jsonl(args.queue_file)
    p2_ids = {r["sample_id"] for r in queue_rows if r.get("review_tier") == "P2"}
    print(f"[1] P2 池总量: {len(p2_ids)} 条")

    # 2. 从 audit 文件取 rejected sample_id
    audit_rows = read_jsonl(args.audit_file)
    rejected_ids = {r["sample_id"] for r in audit_rows if r.get("review_status") == "rejected"}
    accepted_audited = {r["sample_id"] for r in audit_rows if r.get("review_status") == "accepted"}
    pending = {r["sample_id"] for r in audit_rows if r.get("review_status") not in ("accepted", "rejected")}
    print(f"[2] 审核通过: {len(accepted_audited)} | 拒绝: {len(rejected_ids)} | 未标记: {len(pending)}")
    if rejected_ids:
        print(f"    拒绝的 sample_id: {rejected_ids}")
    if pending:
        print(f"    !! 有 {len(pending)} 条未标记 review_status，将按接受处理", file=sys.stderr)

    # 3. 从 labeled_pairs 中筛出 P2 且未被拒绝的行
    all_pairs = read_jsonl(args.pairs_file)
    accepted_p2 = [r for r in all_pairs
                   if r["sample_id"] in p2_ids and r["sample_id"] not in rejected_ids]
    print(f"[3] 接受的 P2 条目: {len(accepted_p2)} 条")

    # 4. 写 P2 merge 文件
    write_jsonl(args.p2_out, accepted_p2)
    print(f"[4] 写出: {args.p2_out}")

    # 5. 合并 baseline + 新 P2
    baseline_rows = read_jsonl(args.baseline_file)
    combined = baseline_rows + accepted_p2
    write_jsonl(args.combined_out, combined)
    print(f"[5] 合并完成: baseline {len(baseline_rows)} + 新P2 {len(accepted_p2)} = {len(combined)} 条")
    print(f"    写出: {args.combined_out}")
    print()
    print("下一步：构建数据集")


if __name__ == "__main__":
    main()
