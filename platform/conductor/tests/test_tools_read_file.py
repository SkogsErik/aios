from pathlib import Path

from tools.read_file import ReadFileTool


class TestReadFileTool:
    def test_name_and_description(self):
        tool = ReadFileTool()
        assert tool.name == "read_file"
        assert tool.description

    def test_parameters_schema(self):
        tool = ReadFileTool()
        assert "path" in tool.parameters["properties"]
        assert "path" in tool.parameters["required"]

    def test_reads_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        tool = ReadFileTool(allowed_prefixes=[tmp_path])
        result = tool.run(path=str(f))
        assert result.success is True
        assert result.output == "hello world"

    def test_file_not_found(self, tmp_path):
        tool = ReadFileTool(allowed_prefixes=[tmp_path])
        result = tool.run(path=str(tmp_path / "nope.txt"))
        assert result.success is False
        assert "not found" in (result.error or "")

    def test_path_traversal_blocked(self, tmp_path):
        tool = ReadFileTool(allowed_prefixes=[tmp_path])
        result = tool.run(path="/etc/passwd")
        assert result.success is False
        assert "denied" in (result.error or "").lower()

    def test_empty_path_error(self):
        tool = ReadFileTool()
        result = tool.run(path="")
        assert result.success is False

    def test_validate_params(self):
        tool = ReadFileTool()
        errors = tool.validate_params({})
        assert "path" in str(errors)

    def test_directory_instead_of_file(self, tmp_path):
        tool = ReadFileTool(allowed_prefixes=[tmp_path])
        result = tool.run(path=str(tmp_path))
        assert result.success is False
        assert "not a file" in (result.error or "").lower()
