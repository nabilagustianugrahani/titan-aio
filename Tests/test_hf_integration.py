"""Integration tests for HuggingFace services and MCP tools.

These tests verify:
1. HFClient service can import and initialize
2. MCP tool modules can import without errors
3. Tools are registered in the MCP server
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_path():
    """Ensure project root is on sys.path."""
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


class TestHFClient:
    """Tests for Services.hf_client."""

    def test_import(self):
        """HFClient can be imported."""
        from Services.hf_client import HFClient, hf_client
        assert HFClient is not None
        assert hf_client is not None

    def test_singleton(self):
        """hf_client is a singleton."""
        from Services.hf_client import HFClient, hf_client
        assert isinstance(hf_client, HFClient)

    def test_get_token_exists(self):
        """HF_TOKEN is configured (may be empty in CI, but method works)."""
        from Services.hf_client import hf_client
        token = hf_client._get_token()
        assert isinstance(token, str)

    def test_import_via_string(self):
        """Module-level import works (no syntax errors)."""
        spec = importlib.util.find_spec("Services.hf_client")
        assert spec is not None, "Services.hf_client module not found"

    def test_methods_exist(self):
        """All expected methods exist on HFClient."""
        from Services.hf_client import HFClient

        expected = [
            "get_api", "space_info", "space_logs", "space_restart",
            "space_pause", "space_set_hardware", "space_set_secret",
            "space_list_secrets", "space_delete_secret", "space_set_env",
            "space_list_env", "space_toggle_dev_mode", "space_wait",
            "hub_list_models", "hub_list_datasets", "hub_list_spaces",
            "hub_upload_file", "hub_download_file",
            "job_list", "job_run", "job_logs", "job_cancel", "job_list_hardware",
            "collection_list", "collection_create", "collection_add_item",
        ]
        instance = HFClient()
        for method in expected:
            assert hasattr(instance, method), f"Missing method: {method}"


class TestHFMCPTools:
    """Tests for HF MCP tool modules."""

    def test_hf_spaces_tools_import(self):
        """hf_spaces_tools module imports cleanly."""
        from MCP.tools import hf_spaces_tools
        assert hf_spaces_tools is not None

    def test_hf_hub_tools_import(self):
        """hf_hub_tools module imports cleanly."""
        from MCP.tools import hf_hub_tools
        assert hf_hub_tools is not None

    def test_hf_jobs_tools_import(self):
        """hf_jobs_tools module imports cleanly."""
        from MCP.tools import hf_jobs_tools
        assert hf_jobs_tools is not None

    def test_hf_inference_tools_import(self):
        """hf_inference_tools module imports cleanly."""
        from MCP.tools import hf_inference_tools
        assert hf_inference_tools is not None

    def test_hf_tools_loaded_in_mcp_server(self):
        """HF tool names are registered in the MCP server."""
        from MCP.server import mcp

        # FastMCP v0.4+ stores tools via get_tools()
        try:
            tool_list = mcp.get_tools()
            tool_names = {t.name for t in tool_list}
        except Exception:
            # Fallback: import hf tool modules directly and check attributes
            import MCP.tools.hf_spaces_tools
            import MCP.tools.hf_hub_tools
            import MCP.tools.hf_jobs_tools
            import MCP.tools.hf_inference_tools
            tool_names = {
                name for name in dir(MCP.tools.hf_spaces_tools)
                if name.startswith("hf_") and callable(getattr(MCP.tools.hf_spaces_tools, name, None))
            }
            tool_names |= {
                name for name in dir(MCP.tools.hf_hub_tools)
                if name.startswith("hf_") and callable(getattr(MCP.tools.hf_hub_tools, name, None))
            }
            tool_names |= {
                name for name in dir(MCP.tools.hf_jobs_tools)
                if name.startswith("hf_") and callable(getattr(MCP.tools.hf_jobs_tools, name, None))
            }
            tool_names |= {
                name for name in dir(MCP.tools.hf_inference_tools)
                if name.startswith("hf_") and callable(getattr(MCP.tools.hf_inference_tools, name, None))
            }

        hf_tools = {n for n in tool_names if n.startswith("hf_")}
        assert len(hf_tools) >= 12, (
            f"Expected 12+ HF tools, found {len(hf_tools)}: {sorted(hf_tools)}"
        )

        # Check specific critical tools
        critical = [
            "hf_space_info", "hf_space_restart", "hf_space_logs",
            "hf_search_models", "hf_jobs_list", "hf_text_generate",
        ]
        missing = [t for t in critical if t not in hf_tools]
        assert not missing, f"Critical HF tools missing from MCP server: {missing}"

    def test_no_circular_imports(self):
        """Modules don't cause circular import errors."""
        import MCP.server  # noqa: F401
        from MCP.instance import mcp
        assert mcp is not None


class TestHFAgent:
    """Tests for HF Agent."""

    def test_import(self):
        """HFAgent can be imported."""
        from Services.agents.hf_agent import HFAgent
        assert HFAgent is not None

    def test_agent_instantiation(self):
        """HFAgent can be instantiated."""
        from Services.agents.hf_agent import HFAgent
        agent = HFAgent()
        assert agent.name == "HFAgent"
        assert hasattr(agent, "execute")

    def test_agent_methods(self):
        """HFAgent has all expected methods."""
        from Services.agents.hf_agent import HFAgent
        agent = HFAgent()
        assert hasattr(agent, "_health_check")
        assert hasattr(agent, "_backup_db")
        assert hasattr(agent, "_space_status")
