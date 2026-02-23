"""Tests for FastAPI routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def client():
    from app.api.server import app
    return TestClient(app)


class TestHealthRoutes:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "CodeCraft AI"
        assert "models" in data

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestFileRoutes:
    def test_list_files(self, client):
        r = client.get("/api/files/list")
        assert r.status_code == 200
        assert "files" in r.json()

    def test_write_and_read_file(self, client, tmp_path):
        # Write
        r = client.post("/api/files/write", json={
            "path": "test_api_file.py",
            "content": "# test\nprint('hello')\n",
        })
        assert r.status_code == 200
        assert r.json()["success"] is True

        # Read
        r = client.get("/api/files/read", params={"path": "test_api_file.py"})
        assert r.status_code == 200
        assert "print('hello')" in r.json()["content"]

    def test_run_python_code(self, client):
        r = client.post("/api/files/run", json={
            "code": "print('from test')",
            "language": "python",
        })
        assert r.status_code == 200
        result = r.json()
        assert result["success"] is True
        assert "from test" in result["output"]

    def test_lint_valid_code(self, client):
        r = client.post("/api/files/lint", json={
            "code": "x = 1\n",
            "language": "python",
        })
        assert r.status_code == 200
        assert r.json()["valid"] is True


class TestChatRoutes:
    def test_chat_message_mocked(self, client):
        with patch("app.api.routes.chat.agent") as mock_agent:
            mock_agent.chat = AsyncMock(return_value="Hello from AI!")
            r = client.post("/api/chat/message", json={
                "prompt": "Hello",
                "model": "claude",
                "messages": [],
            })
            assert r.status_code == 200
            assert r.json()["response"] == "Hello from AI!"

    def test_explain_code(self, client):
        with patch("app.api.routes.chat.agent") as mock_agent:
            mock_agent.explain_code = AsyncMock(return_value="This code prints hello")
            r = client.post("/api/chat/explain", json={
                "code": "print('hello')",
                "model": "claude",
            })
            assert r.status_code == 200
            assert "explanation" in r.json()

    def test_fix_code(self, client):
        with patch("app.api.routes.chat.agent") as mock_agent:
            mock_agent.analyze_and_fix = AsyncMock(return_value="Fixed: print('hello')")
            r = client.post("/api/chat/fix", json={
                "code": "prnt('hello')",
                "error": "NameError: name 'prnt' is not defined",
                "model": "claude",
            })
            assert r.status_code == 200
            assert "fixed_code" in r.json()
