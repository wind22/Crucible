"""命令行入口。

用法：
  crucible instances                      # 列出内置领域实例
  crucible run pure-reasoning "命题…"      # 对一个问题运行辩证循环
    [--premise "…"] [--premises-file f]   # 前提（可多次）
    [--level L1|L2|L3|L4]                 # 能力等级 → 辩证深度（默认 L2）
    [--model claude-opus-4-8]             # LLM 模型
    [--output out.json]                   # 完整结果（含审计追踪）写入文件
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crucible import __version__
from crucible.convergence import LEVELS
from crucible.engine import DialecticalEngine
from crucible.instance import InstanceError, list_bundled_instances, load_instance
from crucible.llm import DEFAULT_MODEL, AnthropicLLM
from crucible.schema import EngineResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crucible",
        description="Crucible 辩证引擎：把想法扔进去，高温煅烧。",
    )
    parser.add_argument("--version", action="version", version=f"crucible {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("instances", help="列出内置领域实例")

    run = sub.add_parser("run", help="对一个问题运行辩证循环")
    run.add_argument("instance", help="领域实例名（如 pure-reasoning）或实例 JSON 文件路径")
    run.add_argument("question", help="待辩证的问题或命题")
    run.add_argument(
        "--premise",
        action="append",
        default=[],
        metavar="TEXT",
        help="一条前提（可多次给出）",
    )
    run.add_argument(
        "--premises-file",
        metavar="FILE",
        help="前提文件：每行一条前提（空行与 # 开头的行被忽略）",
    )
    run.add_argument(
        "--level",
        choices=sorted(LEVELS),
        default="L2",
        help="能力等级 → 辩证深度（默认 L2）",
    )
    run.add_argument("--model", default=DEFAULT_MODEL, help=f"LLM 模型（默认 {DEFAULT_MODEL}）")
    run.add_argument("--max-tokens", type=int, default=16000, help="单次角色调用的输出上限")
    run.add_argument("--output", metavar="FILE", help="将完整结果（含审计追踪）写入 JSON 文件")
    run.add_argument("--quiet", action="store_true", help="不输出过程事件")
    return parser


def _read_premises(args: argparse.Namespace) -> list[str]:
    premises = list(args.premise)
    if args.premises_file:
        for line in Path(args.premises_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                premises.append(line)
    return premises


def _print_summary(result: EngineResult) -> None:
    print()
    print("=" * 60)
    print(f"问题：{result.question}")
    print(f"实例：{result.domain}    终止：{result.termination}    轮数：{len(result.rounds)}")
    print("=" * 60)
    if result.surviving_propositions:
        print("\n【幸存的命题】")
        for p in result.surviving_propositions:
            print(f"- [{p['strength']}] {p['proposition']}")
            for c in p["challenges_survived"]:
                print(f"    ↳ 幸存于：{c}")
    else:
        print("\n【幸存的命题】无——没有命题在攻击中幸存。")
    if result.refuted_propositions:
        print("\n【被驳斥的命题】")
        for p in result.refuted_propositions:
            print(f"- {p['proposition']}")
            print(f"    驳斥：{p['refutation']}")
            if p["lesson"]:
                print(f"    教训：{p['lesson']}")
    if result.epistemic_gains:
        print("\n【认知增益】")
        for g in result.epistemic_gains:
            print(f"- {g}")
    if result.unresolved_tensions:
        print("\n【未解决的张力】")
        for t in result.unresolved_tensions:
            print(f"- {t}")
    if result.framework_critique:
        print(f"\n【框架评价】\n{result.framework_critique}")
    print(f"\n【置信度】{result.confidence}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "instances":
        for name in list_bundled_instances():
            instance = load_instance(name)
            print(f"{name:24s} {instance.name} —— {instance.description}")
        return 0

    # run
    try:
        instance = load_instance(args.instance)
    except InstanceError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 2

    depth = LEVELS[args.level]
    try:
        llm = AnthropicLLM(model=args.model, max_tokens=args.max_tokens, effort=depth.effort)
    except Exception as e:  # SDK 未安装 / 无凭据
        print(f"错误：无法初始化 Anthropic 客户端：{e}", file=sys.stderr)
        print("请安装 anthropic 并设置 ANTHROPIC_API_KEY。", file=sys.stderr)
        return 2

    on_event = (lambda _msg: None) if args.quiet else (lambda msg: print(f"  {msg}", flush=True))
    engine = DialecticalEngine(llm=llm, instance=instance, depth=depth, on_event=on_event)

    print(f"Crucible {__version__} · 实例 {instance.domain} · 等级 {args.level}"
          f"（≤{depth.max_rounds} 轮，N={depth.n_no_weakening}，M={depth.m_no_novelty}）")
    result = engine.run(args.question, _read_premises(args))

    _print_summary(result)
    if args.output:
        Path(args.output).write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n完整结果（含审计追踪）已写入 {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
