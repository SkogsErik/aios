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

    @patch("urllib.request.urlopen")
    def test_parse_results(self, mock_urlopen):
        mock_html = """\
<html><body>
<div class="result__body">
<a class="result__a" href="https://example.com">Example Title</a>
<a class="result__snippet">This is a snippet of the result.</a>
</div>
<div class="result__body">
<a class="result__a" href="https://test.org">Second Result</a>
<a class="result__snippet">Another snippet here.</a>
</div>
</body></html>"""
        mock_response = MagicMock()
        mock_response.read.return_value = mock_html.encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        tool = WebSearchTool()
        result = tool.run(query="test query")
        assert result.success is True
        assert "Example Title" in result.output
        assert "Second Result" in result.output

    @patch("urllib.request.urlopen")
    def test_no_results(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html><body>no results</body></html>"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        tool = WebSearchTool()
        result = tool.run(query="zzzzzznonexistent")
        assert result.success is True
        assert "no results" in result.output.lower()

    def test_validate_params(self):
        tool = WebSearchTool()
        errors = tool.validate_params({})
        assert "query" in str(errors)
