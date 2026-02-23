"""Tests for CodeCraft AI tools."""
import pytest
import asyncio
import os
import tempfile
from pathlib import Path


@pytest.fixture
def temp_workspace(tmp_path):
    return str(tmp_path)


class TestFileTools:
    @pytest.mark.asyncio
    async def test_write_and_read_file(self, temp_workspace):
        from app.tools.file_tools import FileTools
        tools = FileTools(base_path=temp_workspace)
        result = await tools.write_file("test.py", "print('hello')")
        assert result["lines"] == 1
        content = await tools.read_file("test.py")
        assert content == "print('hello')"

    @pytest.mark.asyncio
    async def test_list_files(self, temp_workspace):
        from app.tools.file_tools import FileTools
        tools = FileTools(base_path=temp_workspace)
        await tools.write_file("a.py", "pass")
        await tools.write_file("b.js", "const x = 1;")
        files = await tools.list_files()
        names = [f["name"] for f in files]
        assert "a.py" in names
        assert "b.js" in names

    @pytest.mark.asyncio
    async def test_delete_file(self, temp_workspace):
        from app.tools.file_tools import FileTools
        tools = FileTools(base_path=temp_workspace)
        await tools.write_file("del.py", "pass")
        deleted = await tools.delete_file("del.py")
        assert deleted is True
        files = await tools.list_files()
        assert not any(f["name"] == "del.py" for f in files)

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, temp_workspace):
        from app.tools.file_tools import FileTools
        tools = FileTools(base_path=temp_workspace)
        with pytest.raises(ValueError):
            await tools.read_file("../../etc/passwd")

    def test_get_language(self, temp_workspace):
        from app.tools.file_tools import FileTools
        tools = FileTools(base_path=temp_workspace)
        assert tools.get_language("app.py") == "python"
        assert tools.get_language("index.ts") == "typescript"
        assert tools.get_language("style.css") == "css"
        assert tools.get_language("unknown.xyz") == "text"

    @pytest.mark.asyncio
    async def test_search_in_files(self, temp_workspace):
        from app.tools.file_tools import FileTools
        tools = FileTools(base_path=temp_workspace)
        await tools.write_file("search_test.py", "def hello_world():\n    pass\n")
        results = await tools.search_in_files("hello_world")
        assert len(results) > 0
        assert results[0]["file"] == "search_test.py"


class TestTestTools:
    @pytest.mark.asyncio
    async def test_run_python_code(self):
        from app.tools.test_tools import TestTools
        tools = TestTools()
        result = await tools.run_code_snippet("print('hello')", "python")
        assert result["success"] is True
        assert "hello" in result["output"]

    @pytest.mark.asyncio
    async def test_run_failing_code(self):
        from app.tools.test_tools import TestTools
        tools = TestTools()
        result = await tools.run_code_snippet("raise ValueError('test error')", "python")
        assert result["success"] is False
        assert "ValueError" in result["error"]

    @pytest.mark.asyncio
    async def test_lint_valid_python(self):
        from app.tools.test_tools import TestTools
        tools = TestTools()
        result = await tools.lint_code("x = 1\ny = 2\n", "python")
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_lint_invalid_python(self):
        from app.tools.test_tools import TestTools
        tools = TestTools()
        result = await tools.lint_code("def broken(\n    pass", "python")
        assert result["valid"] is False


class TestImageTools:
    def test_validate_valid_image(self):
        from app.tools.image_tools import ImageTools
        tools = ImageTools()
        # Should not raise
        tools.validate(b"x" * 100, "image/png")

    def test_validate_invalid_type(self):
        from app.tools.image_tools import ImageTools
        tools = ImageTools()
        with pytest.raises(ValueError):
            tools.validate(b"x" * 100, "application/pdf")

    def test_validate_too_large(self):
        from app.tools.image_tools import ImageTools
        tools = ImageTools()
        with pytest.raises(ValueError):
            tools.validate(b"x" * (25 * 1024 * 1024), "image/png")

    def test_to_base64(self):
        from app.tools.image_tools import ImageTools
        import base64
        tools = ImageTools()
        data = b"test data"
        b64 = tools.to_base64(data)
        assert base64.b64decode(b64) == data
