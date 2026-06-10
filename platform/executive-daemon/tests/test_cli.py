"""
test_cli.py — Tests for CLI command parsing and dispatch.
"""

from cli import build_parser


class TestCLIParsing:
    def test_start_parses(self):
        parser = build_parser()
        args = parser.parse_args(["start"])
        assert args.command == "start"

    def test_stop_parses(self):
        parser = build_parser()
        args = parser.parse_args(["stop"])
        assert args.command == "stop"

    def test_status_parses(self):
        parser = build_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_observe_parses(self):
        parser = build_parser()
        args = parser.parse_args(["observe", "did something", "--project", "PRJ-001"])
        assert args.command == "observe"
        assert " ".join(args.text) == "did something"
        assert args.project == "PRJ-001"

    def test_observe_with_energy(self):
        parser = build_parser()
        args = parser.parse_args(["observe", "coded", "--energy", "high"])
        assert args.energy == "high"

    def test_patterns_parses(self):
        parser = build_parser()
        args = parser.parse_args(["patterns", "--days", "30"])
        assert args.command == "patterns"
        assert args.days == 30

    def test_pattern_detail_parses(self):
        parser = build_parser()
        args = parser.parse_args(["pattern", "CND-0001", "--accept"])
        assert args.command == "pattern"
        assert args.pattern_id == "CND-0001"
        assert args.accept is True
