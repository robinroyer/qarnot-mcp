📝 FastMCP Qarnot Server: Implementation Roadmap
1. Project Initialization & Specs
[ ] Setup Environment: Initialize a Python 3.10+ project using uv for dependency management.

[ ] Dependency Audit: Add fastmcp, httpx (for Qarnot API calls), pytest, and python-dotenv.

[ ] OpenAPI Ingestion: Review the Qarnot OpenAPI Spec to identify core tools (e.g., list_tasks, create_task, get_status).

2. Core Server Development
[ ] FastMCP Instance: Initialize FastMCP("Qarnot-Manager") configured for streamable-http transport.

[ ] Auth Bridge: Implement a helper function to extract the Authorization: Bearer <token> from the MCP request context and inject it as the X-Api-Key for Qarnot API calls.

[ ] Tool Implementation:

[ ] list_tasks: Tool to fetch and format Qarnot tasks.

[ ] submit_job: Tool to trigger a new computation.

[ ] get_logs: Tool to retrieve specific task outputs.

[ ] Logging & Observability: - [ ] Implement ctx.info() or standard logging to capture user actions (e.g., "User [ID] requested task list").

[ ] Ensure sensitive data (tokens) are filtered from logs.

3. Testing Suite
[ ] Unit Tests: Mock Qarnot API responses using pytest-httpx.

[ ] Integration Tests: Use the FastMCP built-in Client to simulate Claude's HTTP requests.

[ ] Auth Validation: Test that a missing or malformed token returns a clear ToolError.

4. Containerization & Deployment
[ ] Multi-Stage Dockerfile: - [ ] Use a slim Python base image.

[ ] Optimize for size (remove build-tools after uv pip install).

[ ] Deployment Options:

[ ] Production: docker-compose.prod.yml exposing the service on port 8000 with environment variables for Qarnot base URLs.

[ ] Local Tunnel: docker-compose.local.yml that includes a sidecar container (like ngrok or cloudflare-tunnel) to expose the local port to the internet for Claude Web access.

💡 Technical Implementation Guide
To ensure the prompt executes correctly, here are the architectural highlights to include in the code:

Auth Translation Logic
The server must intercept the bearer token. In FastMCP, you access the request context to pull headers:

Python
from fastmcp import FastMCP, Context

mcp = FastMCP("Qarnot")

@mcp.tool()
async def list_qarnot_tasks(ctx: Context):
    # Claude Web sends the token in the Authorization header
    auth_header = ctx.request_context.headers.get("authorization")
    token = auth_header.replace("Bearer ", "") if auth_header else None
    
    # Log action (Clean Code: scannable logging)
    ctx.info(f"Action: list_tasks | User: {ctx.client_id}")
    
    # Use token as Qarnot API Key
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.qarnot.com/tasks", 
            headers={"X-Api-Key": token}
        )
    return response.json()
Docker Strategy
Your docker-compose.local.yml should look like this to support the tunnel requirement:

YAML
services:
  qarnot-mcp:
    build: .
    environment:
      - QARNOT_BASE_URL=https://api.qarnot.com
  
  tunnel:
    image: cloudflare/cloudflared
    command: tunnel --url http://qarnot-mcp:8000
    depends_on:
      - qarnot-mcp
