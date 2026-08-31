# Search Provider API Keys

Priority order: **Tavily (MCP) → DDG (web_search) → SerpAPI (curl) → Serper (curl)**

## Tavily — AI-Native Search (MCP)

Free tier: 1000 queries/month per key. AI-summarized results + content extraction + crawl.

### MCP Setup (preferred)
```bash
# Add as Hermes MCP server (persists in config.yaml)
hermes mcp add tavily --url "https://mcp.tavily.com/mcp/?tavilyApiKey=<key>"
# reply 'n' to auth prompt, 'Y' to enable all 5 tools
```

5 tools: `tavily_search`, `tavily_extract`, `tavily_crawl`, `tavily_map`, `tavily_research`.

### Multi-Key Rotation
Add multiple MCP servers when one key exhausts its quota:
```bash
hermes mcp add tavily-2 --url "https://mcp.tavily.com/mcp/?tavilyApiKey=<key2>"
hermes mcp add tavily-3 --url "https://mcp.tavily.com/mcp/?tavilyApiKey=<key3>"
```
Each adds 5 tools with suffixed names.

### Direct API (fallback)
```bash
curl -s -X POST https://api.tavily.com/search \
  -H "Content-Type: application/json" \
  -d '{"api_key":"<key>","query":"...","search_depth":"basic","max_results":3}'
```

### Comparison
- **Tavily**: AI answer + relevance score (0-1) + content extraction + crawl ✅ best quality
- **Serper**: Google search, position ranking, 2500q free
- **SerpAPI**: Google + Knowledge Graph, 100q free
- **DDG** (web_search): unlimited but basic, no ranking

## Serper — Google Search via API

Free tier: 2500 queries/month. Google results with position ranking, rich snippets.

### Setup
```bash
echo "SERPER_API_KEY=your-key" >> ~/.omniroute/.env
```

### Testing
```bash
curl -s -X POST https://google.serper.dev/search \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q":"test query","num":3}'
```

## SerpAPI — Google + Knowledge Graph

Free tier: 100 queries/month.

### Setup
```bash
echo "SERPAPI_API_KEY=your-key" >> ~/.omniroute/.env
```

### Testing
```bash
curl -s "https://serpapi.com/search?q=test&api_key=$SERPAPI_API_KEY&num=3"
```

## Key Storage
All API keys in `~/.omniroute/.env`. Tavily keys also stored as MCP URLs in Hermes config.yaml.
