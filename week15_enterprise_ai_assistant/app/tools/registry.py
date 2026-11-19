"""Tool registry and dispatcher for function calling."""

import inspect
import json
import logging
from typing import Callable, Dict, Any, List, Optional
from app.tools.builtins import calculate, get_current_datetime, search_web, query_knowledge_base
from app.core.structured_output import ToolExecutionRecord

logger = logging.getLogger("ai_assistant.tool_registry")


class ToolRegistry:
    """Manages registration, schema generation, and execution of callable tools."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def register(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a python function as an AI tool."""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_doc = description or inspect.getdoc(func) or "No description provided."
            
            sig = inspect.signature(func)
            parameters: Dict[str, Any] = {
                "type": "object",
                "properties": {},
                "required": []
            }

            for param_name, param in sig.parameters.items():
                param_type = "string"
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list or param.annotation == List:
                    param_type = "array"
                elif param.annotation == dict or param.annotation == Dict:
                    param_type = "object"

                parameters["properties"][param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name}"
                }

                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)

            self._tools[tool_name] = func
            self._schemas[tool_name] = {
                "name": tool_name,
                "description": tool_doc,
                "parameters": parameters
            }
            logger.info(f"Registered tool: {tool_name}")
            return func
        return decorator

    def _register_default_tools(self):
        """Register built-in tool suite."""
        self.register(name="calculate", description="Safely evaluate math expressions like '2**10 + sqrt(144)'")(calculate)
        self.register(name="get_current_datetime", description="Get current date and time with timezone offset")(get_current_datetime)
        self.register(name="search_web", description="Perform web search for current information")(search_web)
        self.register(name="query_knowledge_base", description="Query vector database for internal documents")(query_knowledge_base)

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return tool schemas in OpenAI/Gemini compatible function format."""
        return list(self._schemas.values())

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionRecord:
        """Safely execute a tool by name with arguments."""
        if tool_name not in self._tools:
            return ToolExecutionRecord(
                tool_name=tool_name,
                arguments=arguments,
                result={"error": f"Tool '{tool_name}' not found in registry."}
            )

        func = self._tools[tool_name]
        try:
            result = func(**arguments)
            return ToolExecutionRecord(
                tool_name=tool_name,
                arguments=arguments,
                result=result
            )
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return ToolExecutionRecord(
                tool_name=tool_name,
                arguments=arguments,
                result={"error": str(e), "status": "failed"}
            )


# Global tool registry instance
tool_registry = ToolRegistry()
