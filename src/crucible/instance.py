"""领域实例（Instance Descriptor）。

内核领域无关；要将其实例化到特定领域，需要加载三样东西
（architecture.md §3、§4.1）：
1. premise_types    —— 什么算有效的输入
2. integrity_rules  —— 什么算不可接受的错误
3. method_market    —— 该领域已知的论证或分析工具
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any


class InstanceError(ValueError):
    """实例描述符不合法。"""


@dataclass(frozen=True)
class PremiseType:
    type: str
    description: str
    validation: str = ""


@dataclass(frozen=True)
class IntegrityRule:
    id: str
    description: str
    checker: str = "challenger"
    severity: str = "blocker"  # blocker | warning


@dataclass(frozen=True)
class Method:
    id: str
    description: str
    when_to_use: str = ""


@dataclass(frozen=True)
class InstanceDescriptor:
    domain: str
    name: str
    description: str
    premise_types: tuple[PremiseType, ...] = ()
    integrity_rules: tuple[IntegrityRule, ...] = ()
    method_market: tuple[Method, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstanceDescriptor":
        for key in ("domain", "name", "description"):
            if not isinstance(data.get(key), str) or not data.get(key):
                raise InstanceError(f"实例描述符缺少必填字段：{key}")
        try:
            premise_types = tuple(
                PremiseType(
                    type=p["type"],
                    description=p["description"],
                    validation=p.get("validation", ""),
                )
                for p in data.get("premise_types", [])
            )
            integrity_rules = tuple(
                IntegrityRule(
                    id=r["id"],
                    description=r["description"],
                    checker=r.get("checker", "challenger"),
                    severity=r.get("severity", "blocker"),
                )
                for r in data.get("integrity_rules", [])
            )
            method_market = tuple(
                Method(
                    id=m["id"],
                    description=m["description"],
                    when_to_use=m.get("when_to_use", ""),
                )
                for m in data.get("method_market", [])
            )
        except KeyError as e:  # pragma: no cover - message path
            raise InstanceError(f"实例描述符条目缺少字段：{e}") from e
        if not premise_types:
            raise InstanceError("实例描述符至少需要一个 premise_type")
        if not integrity_rules:
            raise InstanceError("实例描述符至少需要一条 integrity_rule")
        return cls(
            domain=data["domain"],
            name=data["name"],
            description=data["description"],
            premise_types=premise_types,
            integrity_rules=integrity_rules,
            method_market=method_market,
        )

    @classmethod
    def from_json(cls, text: str) -> "InstanceDescriptor":
        return cls.from_dict(json.loads(text))


def _bundled_dir():
    return resources.files("crucible") / "instances"


def list_bundled_instances() -> list[str]:
    """列出内置实例的 domain 名。"""
    names = []
    for entry in _bundled_dir().iterdir():
        if entry.name.endswith(".json"):
            names.append(entry.name[: -len(".json")].replace("_", "-"))
    return sorted(names)


def load_instance(name_or_path: str) -> InstanceDescriptor:
    """加载实例：先按内置 domain 名找，找不到再当文件路径读。"""
    bundled = _bundled_dir() / (name_or_path.replace("-", "_") + ".json")
    if bundled.is_file():
        return InstanceDescriptor.from_json(bundled.read_text(encoding="utf-8"))
    path = Path(name_or_path)
    if path.is_file():
        return InstanceDescriptor.from_json(path.read_text(encoding="utf-8"))
    raise InstanceError(
        f"找不到实例 {name_or_path!r}。内置实例：{', '.join(list_bundled_instances())}"
    )
