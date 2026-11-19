"""Unit tests for tool calling and execution registry."""

import pytest
from app.tools.builtins import calculate, get_current_datetime, search_web
from app.tools.registry import tool_registry


def test_calculate_tool():
    res = calculate("2**8 + sqrt(144)")
    assert res["status"] == "success"
    assert res["result"] == 256 + 12

    # Malicious or invalid expression handled gracefully
    bad_res = calculate("import os; os.system('ls')")
    assert bad_res.get("status") == "failed" or "error" in bad_res


def test_datetime_tool():
    res = get_current_datetime(timezone_offset_hours=0)
    assert res["status"] == "success"
    assert "date" in res
    assert "time" in res


def test_search_web_tool():
    res = search_web("vLLM serving engine")
    assert res["status"] == "success"
    assert len(res["results"]) > 0


def test_tool_registry():
    schemas = tool_registry.get_schemas()
    assert len(schemas) >= 3
    tool_names = [s["name"] for s in schemas]
    assert "calculate" in tool_names
    assert "get_current_datetime" in tool_names

    record = tool_registry.execute("calculate", {"expression": "50 * 20"})
    assert record.tool_name == "calculate"
    assert record.result["result"] == 1000
