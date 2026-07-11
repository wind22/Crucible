from crucible.cli import build_parser, main


def test_instances_command_lists_bundled(capsys):
    assert main(["instances"]) == 0
    out = capsys.readouterr().out
    assert "pure-reasoning" in out
    assert "data-analysis" in out
    assert "strategic-simulation" in out


def test_run_parser_defaults():
    args = build_parser().parse_args(["run", "pure-reasoning", "一个问题"])
    assert args.instance == "pure-reasoning"
    assert args.question == "一个问题"
    assert args.level == "L2"
    assert args.premise == []


def test_run_unknown_instance_fails_cleanly(capsys):
    assert main(["run", "no-such-instance", "问题"]) == 2
    err = capsys.readouterr().err
    assert "找不到实例" in err
