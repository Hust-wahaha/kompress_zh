from __future__ import annotations

"""
将 Claude Code 对话批量导出为 kompress_zh 训练源文件

用途：
  从 Claude Code（~/.claude/projects/）中提取中文文本，
  生成 session_chunk 类型的源文档，供 build_dataset.py source-pool 处理。

快速上手（PowerShell，可直接复制粘贴）：
  # 最简调用（使用默认路径）
  python scripts/export_conversations.py

  # 指定自定义路径
  python scripts/export_conversations.py `
    --projects-dir "D:/yanyi/.claude/projects" `
    --output-dir data/raw/source_docs/sessions_v1

  # 只导出包含 "kompress" 的项目，预览不写文件
  python scripts/export_conversations.py --project-filter kompress --dry-run

下一步：
  python scripts/build_dataset.py source-pool `
    --input-dir data/raw/source_docs/sessions_v1 `
    --source-pool-tag source_pool_sessions_v1 `
    --source-type session_chunk

各组员配置：
  1. 修改 --projects-dir 为自己的 Claude Code 目录
  2. 在 DEFAULT_REDACT_PATTERNS 底部追加自定义隐私规则
  3. 如需排除某些项目，使用 --project-filter 或 --exclude-project
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ─── 隐私清洗规则 ──────────────────────────────────────────────────────────────
# 格式：(正则模式, 替换文本)
# 各组员可在列表末尾追加自定义规则，无需修改其他代码
DEFAULT_REDACT_PATTERNS: list[tuple[str, str]] = [
    # API 密钥 / Token
    (r"sk-[A-Za-z0-9]{20,}", "[API_KEY]"),
    (r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}", "Bearer [TOKEN]"),
    (r"(?i)api[_\-]?key\s*[:=]\s*\S+", "api_key=[REDACTED]"),
    # 邮箱地址
    (r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", "[邮箱]"),
    # Windows 路径中的用户名（C:\Users\name\ → C:\Users\[USER]\）
    (r"(?i)([A-Za-z]:\\[Uu]sers\\)[^\\\s/，。；：]+", r"\1[USER]"),
    # Linux / Mac 家目录（/home/name/ 或 /Users/name/）
    (r"(/home/)[^/\s，。；：]+", r"\1[USER]"),
    (r"(/Users/)[^/\s，。；：]+", r"\1[USER]"),
    # 中国大陆手机号（1 开头 11 位）
    (r"\b1[3-9]\d{9}\b", "[手机号]"),
    # 身份证号（18 位）
    (r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b", "[证件号]"),
    # 内网 IP
    (r"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b", "[内网IP]"),

    # ── 在此处追加自定义规则 ──────────────────────────────
    # 示例：(r"公司名称", "[单位]"),
]

# ─── 可调阈值 ─────────────────────────────────────────────────────────────────
_DEFAULT_MIN_SEGMENT_ZH = 60    # 单条消息中文字符下限（低于此跳过该条）
_DEFAULT_MIN_SESSION_ZH = 300   # 整个会话中文字符下限（低于此跳过整个文件）


# ─── 文本工具 ─────────────────────────────────────────────────────────────────

def count_chinese(text: str) -> int:
    return sum(1 for ch in text if "一" <= ch <= "鿿")


def strip_fenced_code(text: str) -> str:
    """去掉多行代码块（```...```），保留行内反引号（anchor 锚点）。"""
    return re.sub(r"```[\s\S]*?```", "\n", text)


# Claude Code IDE 注入的系统标签白名单（需整块去除）
_SYSTEM_TAG_NAMES = (
    "ide_opened_file",
    "ide_selection",
    "system-reminder",
    "user-prompt-submit-hook",
    "command-name",
    "antml:function_calls",
    "antml:invoke",
    "antml:parameter",
)
_SYSTEM_TAG_RE = re.compile(
    r"<(?:" + "|".join(re.escape(t) for t in _SYSTEM_TAG_NAMES) + r")[^>]*>[\s\S]*?</(?:"
    + "|".join(re.escape(t) for t in _SYSTEM_TAG_NAMES)
    + r")>",
    re.IGNORECASE,
)
# 未闭合的单行系统标签（如 <ide_opened_file> 后面没有对应闭合标签的情况）
_ORPHAN_TAG_RE = re.compile(
    r"<(?:" + "|".join(re.escape(t) for t in _SYSTEM_TAG_NAMES) + r")[^>]*>",
    re.IGNORECASE,
)
# Markdown 表格行（| ... | 格式）
_TABLE_ROW_RE = re.compile(r"^\|.*\|[ \t]*$", re.MULTILINE)
_TABLE_SEP_RE = re.compile(r"^\|[-| :]+\|[ \t]*$", re.MULTILINE)


def strip_system_noise(text: str) -> str:
    """去掉 Claude Code IDE 注入的系统标签和 Markdown 表格。"""
    text = _SYSTEM_TAG_RE.sub("", text)
    text = _ORPHAN_TAG_RE.sub("", text)
    # 去掉 markdown 表格（表头、分割线、数据行）
    text = _TABLE_ROW_RE.sub("", text)
    text = _TABLE_SEP_RE.sub("", text)
    return text


def apply_redaction(text: str, patterns: list[tuple[str, str]]) -> str:
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def normalize_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def is_subsumed(shorter_texts: list[str], longer_texts: list[str]) -> bool:
    """shorter 的正文序列是否是 longer 的前缀（含完全相同）。

    用于处理 Claude Code"上下文重启"场景：同一项目下，新 session 的开头
    与旧 session 完全重复，但后续有新内容。此时旧 session 被新 session
    完全覆盖，只保留更长的那个，避免几乎相同的内容重复进入 source pool。
    """
    return len(longer_texts) >= len(shorter_texts) and longer_texts[: len(shorter_texts)] == shorter_texts


def fmt_ts(ts_str: str) -> str:
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts_str[:16] if ts_str else ""


# ─── 消息提取 ─────────────────────────────────────────────────────────────────

def extract_text(content: list | str) -> str:
    """从 content 字段中提取纯文本块，跳过 tool_use / tool_result / thinking。"""
    if isinstance(content, str):
        return content.strip()
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts).strip()


def is_user_turn(entry: dict) -> bool:
    """判断是否为用户真实输入（排除 tool_result 回调）。"""
    if entry.get("type") != "user":
        return False
    content = entry.get("message", {}).get("content", [])
    if not content:
        return False
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                return False
    return True


def is_assistant_turn(entry: dict) -> bool:
    return entry.get("type") == "assistant"


# ─── 会话处理 ─────────────────────────────────────────────────────────────────

def read_session(path: Path) -> list[dict]:
    entries: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def extract_segments(
    entries: list[dict],
    *,
    include_user: bool,
    redact_patterns: list[tuple[str, str]],
    min_zh: int,
) -> list[tuple[str, str, str]]:
    """
    返回 list of (role, timestamp, cleaned_text)。

    只保留中文字符 >= min_zh 的消息段。
    """
    segments: list[tuple[str, str, str]] = []
    for entry in entries:
        ts = fmt_ts(entry.get("timestamp", ""))
        role = ""

        if include_user and is_user_turn(entry):
            role = "user"
            raw = extract_text(entry.get("message", {}).get("content", []))
        elif is_assistant_turn(entry):
            role = "assistant"
            raw = extract_text(entry.get("message", {}).get("content", []))
        else:
            continue

        if not raw:
            continue

        cleaned = strip_system_noise(raw)   # 先去 IDE 注入标签
        cleaned = strip_fenced_code(cleaned)
        if redact_patterns:
            cleaned = apply_redaction(cleaned, redact_patterns)
        cleaned = normalize_blank_lines(cleaned)

        if count_chinese(cleaned) >= min_zh:
            segments.append((role, ts, cleaned))

    return segments


def build_md(
    segments: list[tuple[str, str, str]],
    *,
    session_id: str,
    project_name: str,
    first_ts: str,
) -> str:
    """
    输出格式说明：
    - 角色/时间戳信息放进 HTML 注释（<!-- role=... -->），不是裸文本标签。
      build_dataset.py 的 strip_markdown_noise() 会剥除所有 <!-- ... -->，
      所以这些标签不会进入 source pool 的 original_text——实际压缩场景中
      不会出现"【用户】/【助手】"这类格式 token，不能让它污染训练分布。
    - 正文与注释之间留一个空行，使 paragraphize() 正确切段。

    保留行内反引号（`file.py`、`--flag` 等）作为 anchor 锚点，
    供 DeepSeek teacher 标注时判断是否保留。
    """
    lines: list[str] = [
        f"<!-- session={session_id[:12]} project={project_name} ts={first_ts} -->",
        "",
    ]
    for role, ts, text in segments:
        lines.append(f"<!-- role={role} ts={ts} -->")
        lines.append("")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


# ─── 单文件入口 ───────────────────────────────────────────────────────────────

class SessionCandidate(NamedTuple):
    jsonl_path: Path
    project_name: str
    segments: list[tuple[str, str, str]]
    first_ts: str
    total_zh: int

    @property
    def texts(self) -> list[str]:
        return [text for _, _, text in self.segments]


def collect_session(
    jsonl_path: Path,
    project_name: str,
    *,
    include_user: bool,
    redact_patterns: list[tuple[str, str]],
    min_session_zh: int,
    min_segment_zh: int,
) -> SessionCandidate | str:
    """读取并清洗单个 .jsonl 会话。满足条件返回候选对象，否则返回状态描述字符串。"""
    entries = read_session(jsonl_path)
    if not entries:
        return "empty"

    first_ts = fmt_ts(entries[0].get("timestamp", ""))
    segments = extract_segments(
        entries,
        include_user=include_user,
        redact_patterns=redact_patterns,
        min_zh=min_segment_zh,
    )
    if not segments:
        return "no_chinese_segments"

    total_zh = sum(count_chinese(text) for _, _, text in segments)
    if total_zh < min_session_zh:
        return f"too_short({total_zh}zh)"

    return SessionCandidate(
        jsonl_path=jsonl_path,
        project_name=project_name,
        segments=segments,
        first_ts=first_ts,
        total_zh=total_zh,
    )


def resolve_candidates(
    candidates: list[SessionCandidate],
) -> list[tuple[SessionCandidate, str | None]]:
    """同项目内按"前缀覆盖"规则去重。

    Claude Code 的"上下文重启"会产生开头完全相同、后续内容更长的新 session。
    按 segment 数从多到少排序，若某 session 的正文序列是已保留的更长 session
    的前缀（含完全相同），则视为被覆盖，只保留更长的那个。
    返回顺序与输入一致，每项附带 (candidate, superseded_by_stem_or_None)。
    """
    order = sorted(range(len(candidates)), key=lambda i: -len(candidates[i].segments))
    kept: list[SessionCandidate] = []
    superseded_by: dict[int, str] = {}
    for i in order:
        cur = candidates[i]
        hit = next((k for k in kept if is_subsumed(cur.texts, k.texts)), None)
        if hit is not None:
            superseded_by[i] = hit.jsonl_path.stem
        else:
            kept.append(cur)
    return [(c, superseded_by.get(i)) for i, c in enumerate(candidates)]


def write_session(candidate: SessionCandidate, output_dir: Path) -> None:
    content = build_md(
        candidate.segments,
        session_id=candidate.jsonl_path.stem,
        project_name=candidate.project_name,
        first_ts=candidate.first_ts,
    )
    out_path = output_dir / candidate.project_name / f"{candidate.jsonl_path.stem}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 Claude Code 对话导出为 kompress_zh 训练源文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python scripts/export_conversations.py
  python scripts/export_conversations.py --projects-dir "D:/user/.claude/projects" --output-dir data/raw/source_docs/sessions_v1
  python scripts/export_conversations.py --project-filter kompress --dry-run
  python scripts/export_conversations.py --assistant-only --min-session-chinese 500
        """,
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path.home() / ".claude" / "projects",
        help="Claude Code projects 目录（默认：~/.claude/projects）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT_DIR / "data" / "raw" / "source_docs" / "sessions_v1",
        help="输出目录（默认：data/raw/source_docs/sessions_v1）",
    )
    parser.add_argument(
        "--project-filter",
        type=str,
        default=None,
        help="只处理项目名包含此字符串的目录（大小写不敏感）",
    )
    parser.add_argument(
        "--exclude-project",
        type=str,
        nargs="+",
        default=[],
        metavar="NAME",
        help="排除项目名包含这些字符串的目录（可指定多个）",
    )
    parser.add_argument(
        "--assistant-only",
        action="store_true",
        help="只导出助手回复，跳过用户消息（适合提取长篇分析段落）",
    )
    parser.add_argument(
        "--min-segment-chinese",
        type=int,
        default=_DEFAULT_MIN_SEGMENT_ZH,
        help=f"单条消息最少中文字符数，低于此跳过该条（默认：{_DEFAULT_MIN_SEGMENT_ZH}）",
    )
    parser.add_argument(
        "--min-session-chinese",
        type=int,
        default=_DEFAULT_MIN_SESSION_ZH,
        help=f"整个会话最少中文字符数，低于此跳过整个文件（默认：{_DEFAULT_MIN_SESSION_ZH}）",
    )
    parser.add_argument(
        "--no-redact",
        action="store_true",
        help="跳过隐私清洗（仅用于调试，不要用于团队共享）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="统计信息但不写文件",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.projects_dir.exists():
        print(f"[错误] projects 目录不存在：{args.projects_dir}")
        print("       请用 --projects-dir 指定正确路径，例如：")
        print('       --projects-dir "C:\\Users\\yourname\\.claude\\projects"')
        sys.exit(1)

    redact_patterns = [] if args.no_redact else DEFAULT_REDACT_PATTERNS
    include_user = not args.assistant_only
    output_dir = args.output_dir

    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    project_dirs = sorted(d for d in args.projects_dir.iterdir() if d.is_dir())

    if args.project_filter:
        project_dirs = [d for d in project_dirs if args.project_filter.lower() in d.name.lower()]

    if args.exclude_project:
        excludes = [e.lower() for e in args.exclude_project]
        project_dirs = [d for d in project_dirs if not any(ex in d.name.lower() for ex in excludes)]

    stats = {"ok": 0, "skipped": 0, "empty": 0, "superseded": 0}
    skip_detail: dict[str, int] = {}

    for project_dir in project_dirs:
        project_name = project_dir.name
        jsonl_files = sorted(project_dir.glob("*.jsonl"))
        if not jsonl_files:
            continue

        print(f"\n[项目] {project_name}  ({len(jsonl_files)} 个会话)")

        candidates: list[SessionCandidate] = []
        for jf in jsonl_files:
            result = collect_session(
                jf,
                project_name,
                include_user=include_user,
                redact_patterns=redact_patterns,
                min_session_zh=args.min_session_chinese,
                min_segment_zh=args.min_segment_chinese,
            )
            if isinstance(result, str):
                if result == "empty":
                    stats["empty"] += 1
                else:
                    stats["skipped"] += 1
                    skip_detail[result] = skip_detail.get(result, 0) + 1
            else:
                candidates.append(result)

        for cand, superseded_by in resolve_candidates(candidates):
            if superseded_by:
                stats["superseded"] += 1
                print(f"  [skip] {cand.jsonl_path.name}  -> 内容被 {superseded_by}.jsonl 前缀覆盖，跳过")
                continue
            stats["ok"] += 1
            if not args.dry_run:
                write_session(cand, output_dir)
            print(f"  [ok] {cand.jsonl_path.name}  -> segs={len(cand.segments)},zh={cand.total_zh}")

    dry_tag = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{dry_tag}完成")
    print(f"  导出：{stats['ok']} 个会话")
    print(f"  前缀覆盖跳过：{stats['superseded']} 个")
    print(f"  跳过（空）：{stats['empty']} 个")
    print(f"  跳过（过滤）：{stats['skipped']} 个")
    if skip_detail:
        for reason, cnt in sorted(skip_detail.items(), key=lambda x: -x[1]):
            print(f"    {cnt}×  {reason}")

    if not args.dry_run and stats["ok"]:
        rel_out = output_dir.relative_to(ROOT_DIR) if output_dir.is_relative_to(ROOT_DIR) else output_dir
        suggested_tag = f"source_pool_{output_dir.name}"
        print(f"\n输出目录：{output_dir}")
        print("\n下一步——提取 source pool（PowerShell；--source-pool-tag 随 --output-dir 派生，避免多人/多份导出互相覆盖）：")
        print(f"  python scripts/build_dataset.py source-pool `")
        print(f"    --input-dir {rel_out} `")
        print(f"    --source-pool-tag {suggested_tag} `")
        print(f"    --source-type session_chunk")
        print("\n随后校验：")
        print(f"  python scripts/validate_dataset.py data/interim/{suggested_tag}.jsonl --mode source-pool")


if __name__ == "__main__":
    main()
