#!/usr/bin/env python3
"""把实例描述符（src/crucible/instances/*.json）渲染成 skill 参考文件。

JSON 描述符是唯一事实源，Python 引擎与 skill 共享同一份实例定义。
修改实例后运行本脚本重新生成：

    python3 scripts/render_skill_instances.py

tests/test_skill_sync.py 会校验生成文件与 JSON 保持同步。
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "src" / "crucible" / "instances"
OUT_DIR = REPO / "skills" / "crucible" / "references" / "instances"

sys.path.insert(0, str(REPO / "src"))

from crucible.instance import InstanceDescriptor  # noqa: E402


def render(instance: InstanceDescriptor, source_name: str) -> str:
    lines = [
        f"# {instance.name}（{instance.domain}）",
        "",
        f"> 本文件由 scripts/render_skill_instances.py 从 src/crucible/instances/{source_name} 生成，请勿手改。",
        "",
        instance.description,
        "",
        "## 前提类型（什么算有效输入）",
        "",
    ]
    for p in instance.premise_types:
        suffix = f"（校验：{p.validation}）" if p.validation else ""
        lines.append(f"- **{p.type}**：{p.description}{suffix}")
    lines += [
        "",
        "## 完整性约束（什么算不可接受的错误；blocker 级违规直接构成实质性削弱）",
        "",
    ]
    for r in instance.integrity_rules:
        lines.append(f"- **[{r.id}]**（{r.severity}，检查者：{r.checker}）{r.description}")
    if instance.method_market:
        lines += ["", "## 方法市场（按需选用，并在论证中注明所用方法的 id）", ""]
        for m in instance.method_market:
            when = f" —— 适用时机：{m.when_to_use}" if m.when_to_use else ""
            lines.append(f"- **[{m.id}]** {m.description}{when}")
    lines.append("")
    return "\n".join(lines)


def render_all() -> dict[str, str]:
    """返回 {输出文件名: 内容}，供脚本与同步测试共用。"""
    out = {}
    for path in sorted(SRC_DIR.glob("*.json")):
        instance = InstanceDescriptor.from_json(path.read_text(encoding="utf-8"))
        out_name = path.stem.replace("_", "-") + ".md"
        out[out_name] = render(instance, path.name)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in render_all().items():
        (OUT_DIR / name).write_text(content, encoding="utf-8")
        print(f"生成 {OUT_DIR.relative_to(REPO) / name}")


if __name__ == "__main__":
    main()
