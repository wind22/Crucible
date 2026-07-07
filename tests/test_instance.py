import json

import pytest

from crucible.instance import (
    InstanceDescriptor,
    InstanceError,
    list_bundled_instances,
    load_instance,
)


def test_bundled_instances_present():
    names = list_bundled_instances()
    assert names == ["data-analysis", "pure-reasoning", "strategic-simulation"]


def test_bundled_instances_load_and_validate():
    for name in list_bundled_instances():
        instance = load_instance(name)
        assert instance.domain == name
        assert instance.premise_types
        assert instance.integrity_rules
        assert instance.method_market
        # 每条 blocker 规则都有 id 与描述
        for rule in instance.integrity_rules:
            assert rule.id and rule.description
            assert rule.severity in ("blocker", "warning")


def test_load_instance_from_file(tmp_path):
    data = {
        "domain": "custom",
        "name": "自定义实例",
        "description": "测试用",
        "premise_types": [{"type": "t", "description": "d"}],
        "integrity_rules": [{"id": "r1", "description": "d"}],
        "method_market": [],
    }
    path = tmp_path / "custom.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    instance = load_instance(str(path))
    assert instance.domain == "custom"
    assert instance.integrity_rules[0].checker == "challenger"  # 默认值


def test_missing_required_fields_rejected():
    with pytest.raises(InstanceError):
        InstanceDescriptor.from_dict({"domain": "x", "name": "y", "description": "z"})
    with pytest.raises(InstanceError):
        InstanceDescriptor.from_dict(
            {
                "domain": "x",
                "name": "y",
                "description": "z",
                "premise_types": [{"type": "t", "description": "d"}],
                "integrity_rules": [],
            }
        )


def test_unknown_instance_error_lists_bundled():
    with pytest.raises(InstanceError, match="pure-reasoning"):
        load_instance("no-such-instance")
