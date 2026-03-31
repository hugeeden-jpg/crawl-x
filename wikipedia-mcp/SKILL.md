---
name: wikipedia-mcp
description: >
  Access English Wikipedia articles via the wikipedia-data MCP. Use for factual lookups,
  concept explanations, background research, geographic coordinates, and article deep-dives.
  Full article text is cached locally — use the Read tool on the returned file_path to view it.
---

# Wikipedia MCP

English Wikipedia access via `wikipedia-data` MCP. No API key required.

## Tool Overview

| Tool | Description |
|------|-------------|
| `search_wikipedia(query, limit)` | Search and return matching article titles |
| `get_summary(title, sentences)` | Get article intro summary (N sentences) |
| `get_article(title)` | Cache full article to local file, return file_path |
| `get_sections(title)` | List all sections with 500-char preview each |
| `get_links(title, limit)` | List internal Wikipedia links in an article |
| `get_related_topics(title, limit)` | Get related categories and linked articles |
| `extract_key_facts(title, count)` | Extract N key facts as numbered sentences |
| `get_coordinates(title)` | Get latitude/longitude for geographic articles |

## Typical Workflow

**Quick fact lookup:**
```
get_summary("Quantum entanglement", sentences=5)
```

**Deep research on a topic:**
```
1. search_wikipedia("transformer neural network")
2. get_article("Transformer (deep learning)")   # writes to ~/.cache/wikipedia-mcp/
3. Read tool on the returned file_path           # read full content
```

**Explore a topic's structure before reading:**
```
get_sections("Climate change")          # see what sections exist
get_related_topics("Climate change")    # discover adjacent topics
```

**Extract facts for a report:**
```
extract_key_facts("Large language model", count=7)
```

**Geographic lookup:**
```
get_coordinates("Mount Everest")
```

## Handling Ambiguous Titles

When a title is ambiguous (e.g. "Mercury"), tools return a disambiguation list:
```
'Mercury' is ambiguous. Did you mean:
  - Mercury (planet)
  - Mercury (element)
  - Mercury (mythology)
  ...
Re-call with one of the specific titles above.
```
Always use `search_wikipedia` first if unsure of the exact title.

## Full Article Cache

`get_article` writes to `~/.cache/wikipedia-mcp/<Title>.md`.

- File is overwritten on every call (no stale cache)
- Use the `Read` tool with the returned `file_path` to read content
- `char_count` in the response tells you the total size

## Notes

- English Wikipedia only (`lang=en`)
- `get_sections` content previews are truncated at 500 chars per section; use `get_article` for full text
- `get_links` / `get_related_topics` default limit is 50 / 10 respectively
- Response times: summary ~1s, full article ~2-4s depending on article size
