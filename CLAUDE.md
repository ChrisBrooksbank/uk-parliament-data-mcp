# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UK Parliament MCP Server - A Model Context Protocol server that bridges AI assistants with official UK Parliament data APIs. Built with C# .NET 9.0, it provides ~70 tools covering MPs/Lords, bills, votes, committees, Hansard, and more.

## Build Commands

```bash
# Build the project
dotnet build OpenDataMcpServer.sln

# Run the MCP server (stdio transport)
dotnet run --project OpenData.Mcp.Server

# Publish for distribution
dotnet publish OpenData.Mcp.Server -c Release
```

## Architecture

```
AI Assistant ──(MCP/stdio)──> OpenData.Mcp.Server ──(HTTP)──> UK Parliament APIs
```

**Key Components:**

- **Program.cs**: Entry point using .NET Host builder. Registers MCP server with stdio transport, configures DI (IHttpClientFactory, IMemoryCache, logging), uses attribute-based tool discovery via `WithToolsFromAssembly`.

- **Tools/BaseTools.cs**: Abstract base class all tools inherit from. Provides:
  - HTTP request handling with 3-retry exponential backoff
  - 30-second timeout protection
  - URL building with parameter escaping
  - Consistent response format: `{url, data}` or `{url, error, statusCode}`

- **Tools/*Tools.cs**: 15 tool classes (~70 total tools) each targeting a specific Parliament API:
  | Class | API Domain | Purpose |
  |-------|------------|---------|
  | MembersTools | members-api.parliament.uk | MPs, Lords, constituencies, parties |
  | BillsTools | bills-api.parliament.uk | Legislation, amendments, stages |
  | CommonsVotesTools | commonsvotes-api.parliament.uk | Commons divisions |
  | LordsVotesTools | lordsvotes-api.parliament.uk | Lords divisions |
  | CommitteesTools | committees-api.parliament.uk | Committee info, evidence |
  | HansardTools | hansard-api.parliament.uk | Parliamentary record |
  | OralQuestionsTools | oralquestionsandmotions-api.parliament.uk | EDMs, questions |
  | InterestsTools | interests-api.parliament.uk | Register of interests |
  | NowTools | now-api.parliament.uk | Live chamber activity |
  | WhatsOnTools | whatson-api.parliament.uk | Calendar, sessions |
  | StatutoryInstrumentsTools | statutoryinstruments-api.parliament.uk | Acts, SIs |
  | TreatiesTools | treaties-api.parliament.uk | International treaties |
  | ErskineMayTools | erskinemay-api.parliament.uk | Procedure rules |
  | CoreTools | N/A | Session management prompts |

- **Context/**: OpenAPI spec JSON files for each Parliament API (reference documentation)

## Adding New Tools

Follow the established pattern:

```csharp
[McpServerToolType]
public class NewApiTools(IHttpClientFactory httpClientFactory, ILogger<NewApiTools> logger)
    : BaseTools(httpClientFactory, logger)
{
    protected const string NewApiBase = "https://api.parliament.uk";

    [McpServerTool(ReadOnly = true, Idempotent = true),
     Description("Action | keywords, synonyms | Use case | Returns format")]
    public async Task<string> GetSomethingAsync(string param)
    {
        var url = $"{NewApiBase}/endpoint?param={Uri.EscapeDataString(param)}";
        return await GetResult(url);
    }
}
```

Tool descriptions use a 4-part semantic format: `Action | Keywords | Use case | Returns`

## Key Conventions

- **House IDs**: 1 = Commons, 2 = Lords
- **Date format**: YYYY-MM-DD throughout
- **Pagination**: `skip`/`take` parameters where supported
- All tools are read-only and idempotent
- Raw JSON responses from Parliament APIs are passed through (not transformed)
- Tool attributes enable automatic discovery - no manual registration needed

## Dependencies

- ModelContextProtocol (v0.3.0-preview.2)
- Microsoft.Extensions.Hosting (v9.0.5)
- Microsoft.Extensions.Http (v9.0.6)
- Microsoft.Extensions.Caching.Memory (v9.0.5)
