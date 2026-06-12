from unittest.mock import patch, MagicMock
from tools.web_search import WebSearchTool


class TestWebSearchTool:
    def test_name_and_description(self):
        tool = WebSearchTool()
        assert tool.name == "web_search"
        assert tool.description

    def test_empty_query_error(self):
        tool = WebSearchTool()
        result = tool.run(query="")
        assert result.success is False

    @patch("duckduckgo_search.DDGS")
    def test_parse_results(self, mock_ddgs):
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {"title": "Example Title", "body": "This is a snippet of the result.", "href": "https://example.com"},
            {"title": "Second Result", "body": "Another snippet here.", "href": "https://test.org"},
        ]

        tool = WebSearchTool()
        result = tool.run(query="test query")
        assert result.success is True
        assert "Example Title" in result.output
        assert "Second Result" in result.output

    @patch("duckduckgo_search.DDGS")
    def test_no_results(self, mock_ddgs):
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = []

        tool = WebSearchTool()
        result = tool.run(query="zzzzzznonexistent")
        assert result.success is True
        assert "no results" in result.output.lower()

    def test_validate_params(self):
        tool = WebSearchTool()
        errors = tool.validate_params({})
        assert "query" in str(errors)
