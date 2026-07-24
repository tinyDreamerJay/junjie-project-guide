#!/usr/bin/env python3
"""检查项目最低文档、Markdown 链接和常见环境变量覆盖。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote


EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".next",
    ".nuxt",
    ".venv",
    ".vscode",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "vendor",
    "venv",
}

ENV_EXAMPLES = (".env.example", ".env.sample", ".env.template")
HUMAN_ENTRY_FILES = ("README.md",)
COLLABORATION_ENTRY_FILES = ("AGENTS.md", "CONTRIBUTING.md")
CHANGELOG_FILES = ("CHANGELOG.md", "HISTORY.md")
SYSTEM_ENV = {
    "CI",
    "COLORTERM",
    "HOME",
    "LANG",
    "NODE_ENV",
    "PATH",
    "PWD",
    "SHELL",
    "TERM",
    "TMP",
    "TMPDIR",
    "USER",
    "USERNAME",
}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
ENV_DECL_RE = re.compile(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=", re.MULTILINE)
ENV_USE_PATTERNS = (
    re.compile(r"\bprocess\.env\.([A-Z][A-Z0-9_]*)\b"),
    re.compile(r"\bimport\.meta\.env\.([A-Z][A-Z0-9_]*)\b"),
    re.compile(r"\bos\.getenv\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"\bos\.environ(?:\.get\(\s*|\[\s*)['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"\bENV\[\s*['\"]([A-Z][A-Z0-9_]*)['\"]\s*\]"),
    re.compile(r"\bos\.Getenv\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]"),
)


class ChineseArgumentParser(argparse.ArgumentParser):
    def format_help(self) -> str:
        return super().format_help().replace("usage: ", "用法：", 1)

    def format_usage(self) -> str:
        return super().format_usage().replace("usage: ", "用法：", 1)


def parse_args() -> argparse.Namespace:
    parser = ChineseArgumentParser(description=__doc__, add_help=False)
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser.add_argument("root", nargs="?", default=".", help="要检查的仓库根目录")
    parser.add_argument(
        "--ignore-env",
        action="append",
        default=[],
        metavar="NAME",
        help="忽略指定环境变量，可重复使用",
    )
    parser.add_argument(
        "--no-env",
        action="store_true",
        help="跳过环境变量覆盖检查",
    )
    return parser.parse_args()


def is_excluded(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRS for part in parts[:-1])


def iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and not is_excluded(path, root):
            yield path


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return None


def clean_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    else:
        titled_link = re.match(r"^(\S+)\s+(?:['\"(]).*$", target)
        if titled_link:
            target = titled_link.group(1)
    return unquote(target.split("#", 1)[0])


def audit_links(root: Path, files: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        text = read_text(path)
        if text is None:
            continue
        text = FENCE_RE.sub("", text)
        for match in LINK_RE.finditer(text):
            raw_target = match.group(1).strip()
            if not raw_target or raw_target.startswith(("#", "http://", "https://", "mailto:", "data:")):
                continue
            target = clean_link_target(raw_target)
            if not target or "{" in target or "$" in target:
                continue
            resolved = (root / target.lstrip("/\\")).resolve() if target.startswith(("/", "\\")) else (path.parent / target).resolve()
            if not resolved.exists():
                relative_source = path.relative_to(root)
                issues.append(f"{relative_source}：本地链接目标不存在：{raw_target}")
    return issues


def has_named_file(root: Path, names: tuple[str, ...]) -> bool:
    wanted = {name.casefold() for name in names}
    return any(path.is_file() and path.name.casefold() in wanted for path in root.iterdir())


def has_changelog(root: Path) -> bool:
    if has_named_file(root, CHANGELOG_FILES):
        return True
    changelog_dir = root / "docs" / "changelog"
    return changelog_dir.is_dir() and any(
        path.is_file() and path.suffix.lower() == ".md" and path.name.casefold() != "readme.md"
        for path in changelog_dir.iterdir()
    )


def audit_minimum_docs(root: Path) -> list[str]:
    issues: list[str] = []
    if not has_named_file(root, HUMAN_ENTRY_FILES):
        issues.append("项目缺少 README.md 人类入口文档")
    if not has_named_file(root, COLLABORATION_ENTRY_FILES):
        issues.append("项目缺少 AGENTS.md 或 CONTRIBUTING.md 协作入口")
    if not has_changelog(root):
        issues.append("项目缺少 CHANGELOG.md 或 docs/changelog/ 下的实际变更记录")
    return issues


def find_env_example(root: Path) -> Path | None:
    for name in ENV_EXAMPLES:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def audit_env(root: Path, files: list[Path], ignored: set[str]) -> tuple[list[str], str]:
    env_example = find_env_example(root)
    if env_example is None:
        return [], "未找到 .env.example、.env.sample 或 .env.template，已跳过环境变量覆盖检查。"

    example_text = read_text(env_example) or ""
    declared = set(ENV_DECL_RE.findall(example_text))
    used: set[str] = set()

    text_suffixes = {".cjs", ".go", ".js", ".jsx", ".mjs", ".py", ".rb", ".ts", ".tsx", ".vue"}
    for path in files:
        if path.suffix.lower() not in text_suffixes:
            continue
        text = read_text(path)
        if text is None:
            continue
        for pattern in ENV_USE_PATTERNS:
            used.update(pattern.findall(text))

    missing = sorted(used - declared - SYSTEM_ENV - ignored)
    issues = [f"{env_example.name}：缺少代码实际读取的变量：{name}" for name in missing]
    return issues, f"环境变量：代码读取 {len(used)} 个，{env_example.name} 声明 {len(declared)} 个。"


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"错误：仓库根目录不存在或不是目录：{root}", file=sys.stderr)
        return 2

    files = list(iter_files(root))
    minimum_doc_issues = audit_minimum_docs(root)
    link_issues = audit_links(root, files)
    env_issues: list[str] = []
    env_summary = "环境变量覆盖检查已关闭。"
    if not args.no_env:
        env_issues, env_summary = audit_env(root, files, set(args.ignore_env))

    print(f"文档审计：{root}")
    print(f"Markdown 文件：{sum(path.suffix.lower() == '.md' for path in files)}")
    print(env_summary)

    issues = minimum_doc_issues + link_issues + env_issues
    if issues:
        print("\n发现问题：")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("结果：通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
