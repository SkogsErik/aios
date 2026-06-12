from pathlib import Path

from tools.write_file import WriteFileTool


class TestWriteFileTool:
    def test_name_and_description(self):
        tool = WriteFileTool()
        assert tool.name == "write_file"
        assert tool.REQUIRES_CONFIRMATION is True

    def test_writes_new_file(self, tmp_path):
        tool = WriteFileTool(allowed_prefixes=[tmp_path])
        f = tmp_path / "new.txt"
        result = tool.run(path=str(f), content="hello")
        assert result.success is True
        assert f.read_text() == "hello"

    def test_overwrites_existing_file(self, tmp_path):
        tool = WriteFileTool(allowed_prefixes=[tmp_path])
        f = tmp_path / "existing.txt"
        f.write_text("old")
        result = tool.run(path=str(f), content="new")
        assert result.success is True
        assert f.read_text() == "new"

    def test_appends_to_file(self, tmp_path):
        tool = WriteFileTool(allowed_prefixes=[tmp_path])
        f = tmp_path / "appended.txt"
        f.write_text("hello\n")
        result = tool.run(path=str(f), content="world", mode="append")
        assert result.success is True
        assert f.read_text() == "hello\nworld"

    def test_creates_missing_directories(self, tmp_path):
        tool = WriteFileTool(allowed_prefixes=[tmp_path])
        f = tmp_path / "sub" / "deep" / "file.txt"
        result = tool.run(path=str(f), content="nested")
        assert result.success is True
        assert f.read_text() == "nested"

    def test_path_traversal_blocked(self, tmp_path):
        tool = WriteFileTool(allowed_prefixes=[tmp_path])
        result = tool.run(path="/tmp/outside.txt", content="evil")
        assert result.success is False
        assert "denied" in (result.error or "").lower()

    def test_empty_path_error(self):
        tool = WriteFileTool()
        result = tool.run(path="", content="x")
        assert result.success is False

    def test_validate_params(self):
        tool = WriteFileTool()
        errors = tool.validate_params({})
        assert "path" in str(errors)
        assert "content" in str(errors)
