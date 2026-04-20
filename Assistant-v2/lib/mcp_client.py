import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MultiMCPClient:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.server_params: Dict[str, StdioServerParameters] = {}
        self._load_config()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "mcp_config.json")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                for name, server in config.get("mcpServers", {}).items():
                    env = os.environ.copy()
                    if "env" in server:
                        env.update(server["env"])
                    
                    self.server_params[name] = StdioServerParameters(
                        command=server["command"],
                        args=server["args"],
                        env=env
                    )
            print(f"Loaded {len(self.server_params)} MCP servers from config.")
        except Exception as e:
            print(f"Failed to load mcp_config.json: {e}")

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Connects to all servers momentarily to discover their tools.
        In a production environment, you might keep these sessions open.
        """
        all_tools = []
        for name, params in self.server_params.items():
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    # Add server name to tool metadata for easy routing
                    for tool in tools_result.tools:
                        tool_dict = tool.model_dump()
                        tool_dict["server"] = name
                        all_tools.append(tool_dict)
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Calls a specific tool on a specific server.
        """
        if server_name not in self.server_params:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        params = self.server_params[server_name]
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result
