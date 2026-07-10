"""skill 实例参考文件必须与 JSON 描述符（唯一事实源）保持同步。

失败时运行：python3 scripts/render_skill_instances.py
"""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "skills" / "crucible" / "references" / "instances"


def _load_renderer():
    spec = importlib.util.spec_from_file_location(
        "render_skill_instances", REPO / "scripts" / "render_skill_instances.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generated_instance_files_in_sync():
    rendered = _load_renderer().render_all()
    assert rendered, "渲染器没有产出任何实例文件"
    on_disk = {p.name for p in OUT_DIR.glob("*.md")}
    assert on_disk == set(rendered), (
        f"磁盘文件与描述符不一致：多出 {on_disk - set(rendered)}，缺少 {set(rendered) - on_disk}。"
        "请运行 python3 scripts/render_skill_instances.py"
    )
    for name, content in rendered.items():
        actual = (OUT_DIR / name).read_text(encoding="utf-8")
        assert actual == content, (
            f"{name} 与 JSON 描述符不同步，请运行 python3 scripts/render_skill_instances.py"
        )


def test_skill_and_protocol_exist_and_reference_each_other():
    skill = (REPO / "skills" / "crucible" / "SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---")
    assert "name: crucible" in skill
    assert "references/dialectical-protocol.md" in skill
    for domain in ("pure-reasoning", "data-analysis", "strategic-simulation"):
        assert f"references/instances/{domain}.md" in skill

    protocol = (
        REPO / "skills" / "crucible" / "references" / "dialectical-protocol.md"
    ).read_text(encoding="utf-8")
    # 协议覆盖内核四要素：角色、循环、收敛、输出结构
    for anchor in ("三个角色", "循环流程", "收敛纪律", "统一输出结构", "crucible-challenger"):
        assert anchor in protocol
