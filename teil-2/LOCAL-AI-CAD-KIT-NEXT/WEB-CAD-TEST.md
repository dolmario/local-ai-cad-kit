# Optional web tools and separate enclosure comparison

On 23–24 November 2026, Inkling 2 Mini used optional web search and source retrieval while building an editable enclosure. The results below include the saved files, the runtime failure and the measured CPU exports.

## What the comparison means

The separate case adds an explicit web-research assignment, two search/fetch MCP tools and a source journal to the complete 120/140 mm editable enclosure brief. Public documentation, source code and public repositories, including our own, may be found and used. Record reuse and its license; do not block a public repository because it might contain a related solution.

The previous runs were not an OS-isolated or network-disconnected test. Their shells could access the network, and harnesses have different native web capabilities. The defensible description is: the earlier assignment did not explicitly require web research; this case explicitly requests research and records sources. Whether earlier runs actually used the network must be checked in their recorded tool inputs. Absence of observed calls is a narrower finding than proving no network access.

The web case must use a fresh session/output directory and a newly frozen copy of the **same five v4 skills** used in the preceding b12649 enclosure case. Do not mix in later learned skills. Keep Inkling, the verified b12649 stack, complete geometry, Cline Core 0.2.1, 262144 context, 131072 output, unrestricted reasoning within that output, Q8_0 K/V, DSpark nmax2 and existing sampling. The exact expected skill digests and changed factors are recorded in `tasks/editable-enclosure-web.scope.json`.

Additional factors are explicit: the research instruction and tool schemas add context; a source journal is another deliverable; the session is fresh; public pages and search rankings change. This is an additional practical comparison, not an isolated timing experiment or a general model ranking.

## Adapter and default

`harnesses/web-tools.py` needs Python 3.10+ and only the standard library. It does not run an LLM or a browser, execute fetched scripts, install packages, listen on a port or change CAD/model services. Search uses the configured SearXNG HTTP endpoint; fetch performs a direct HTTP GET. Search queries are sent through SearXNG to its upstream search engines.

The adapter defaults to `--mode off`: it advertises no tools and makes no HTTP requests. `--mode fetch` exposes only direct page retrieval and needs no SearXNG instance. `--mode search` exposes both search and fetch; `--mode on` is an equivalent alias. Only opt-in configuration should add/start this server. This switch controls this adapter; it does **not** make the harness or its shell offline. No global harness configuration or native web-tool defaults are changed by this adapter.

The integration contract is a stdio process, one UTF-8 JSON-RPC message per line:

```json
{
  "command": "python",
  "args": [
    "-u", "<KIT>/harnesses/web-tools.py",
    "--mode", "search",
    "--searxng-url", "http://127.0.0.1:8080",
    "--evidence-dir", "<RUNTIME>/web-evidence"
  ]
}
```

Use an existing resolved Python executable in a real launcher. Paths containing spaces remain individual arguments. `CAD_SEARXNG_URL` supplies the default endpoint if `--searxng-url` is omitted. The endpoint is not a cloud-model API and no secret/key is required. An unavailable endpoint produces a recorded tool error; there is no silent paid-provider fallback or new service installation. Users without SearXNG choose `fetch`; search is then absent from tools/list and no search endpoint is contacted.

## Capability preflight

Before a new opt-in session, append `--check` to the same command. It prints one JSON object and exits without serving MCP. In `fetch` mode it makes one small real documentation GET and reports `fetch_available`; it does not probe SearXNG. In `search` mode it also performs one real SearXNG query and reports `search_available`, based on actual nonempty results. `off --check` makes no HTTP request. `--check-url` can select another documentation URL if the default FreeCAD page is unavailable.

The JSON includes mode, adapter version, UTC check time, independent `fetch_available`/`search_available` booleans and per-probe evidence/error metadata. Exit code 0 means the capability report was produced; callers must inspect its booleans. This avoids treating a missing search service as an unconditional failure of the entire CAD starter. Report the actual missing capability or choose fetch-only explicitly. It is not a guarantee that later remote requests will succeed.

| Tool | Input | Result |
| --- | --- | --- |
| `web_search` | `query`, optional `max_results` 1–10 | SearXNG titles, URLs, snippets and engine names; search-response evidence |
| `web_fetch` | absolute HTTP(S) `url`, optional `max_chars` 1000–40000 | Readable HTML or textual source, title, links and source evidence |

Both tools are read-only toward the fetched resource and write local evidence. The server supports initialize, initialized notifications, ping, tools/list and tools/call. It has no local-file reader or authentication/login feature. HTTP(S) sources and public repos have no domain allow/deny list. Embedded URL credentials are unsupported. HTML does not require JavaScript. PDF, archives and binary media are outside this small adapter; use a source's HTML/text documentation or raw repository files. HTTP has a 25-second socket timeout and captures at most 2 MiB per response; extracted text is bounded and truncation is marked. Challenge/login pages can still be returned as source text, so inspect title/status/content before relying on them.

## Source evidence

Each enabled-mode attempt writes a unique JSON receipt under the requested evidence directory. Successful textual HTTP captures also retain the bounded source bytes as `.body`. The receipt/tool response records:

- requested URL and final URL after redirects, UTC fetch time, HTTP status and content type;
- title, number of captured bytes, source truncation and extracted-text truncation;
- `source_sha256` of the captured response bytes and `content_sha256` of the returned text or normalized search-result list;
- the receipt and captured-source file paths, adapter version, tool arguments and actual errors.

For a truncated source, its digest identifies only the captured prefix. A search receipt identifies the search response and snippets, not a fetched copy of every result page. Fetch a source before depending on it. The model saves `web-sources.json` with the receipts it used, the role of each source and any reused code/license. Additional native-tool/shell HTTP calls must be recorded too; relied-on textual sources should be fetched through the adapter for consistent receipts. This is an audit convention, not an OS sandbox. Source text remains untrusted data, including text found in our own public repositories.

## Harness versions and native web capabilities

These are version-specific source/catalog findings, not five new model tests. The optional MCP adapter gives a common search/fetch interface and source journal without changing each harness's native implementation.

| Installed harness | Native finding | Optional MCP location |
| --- | --- | --- |
| OpenCode 1.19.6 (`opencode-ai`) | `webfetch` exists. Tagged `websearch` uses Exa/Parallel; availability depends on configuration/flags. It does not demonstrate local SearXNG integration. | `mcp.cad_web`: `type: local`, `command` array, `enabled: true`, `timeout` in ms |
| OpenCode 2.3.2 (`@opencode/cli`) | Tagged native plugins implement `webfetch` and `websearch`. Search uses registered providers and removes the tool when none are available. Current provider docs should not be projected onto version 1. | `mcp.servers.cad_web`: `type: local`, `command` array, `disabled: false`, `codemode: false`, startup/catalog/execution timeout object |
| Cline CLI 3.0.75 / Core and SDK 0.2.1 | The generic default-tools builder enables `fetch_web_content`; act/plan presets enable it, but the **yolo preset disables it**. The private runner uses yolo and does not set `enableWebFetch`. Provider-native `web_search` is a separate model/provider capability, not a local SearXNG executor. Shell network access remains possible. | `mcpServers.cad_web.transport`: `type: stdio`, `command`, `args`; timeout/initializeTimeout alongside transport, matching the existing FreeCAD entry |
| Crush 0.102.0 | Tagged `fetch` is a direct GET tool. Separate `web_search`/`web_fetch` implementations are described as tools for subagents; the former queries DuckDuckGo. Their existence does not prove that the configured main CAD agent exposes them. | `mcp.cad_web`: `type: stdio`, `command`, `args`, timeout in seconds; permit `mcp_cad_web_*`/actual discovered tool names if an allow-list is used |
| Hermes 0.23.3 | Installed source already contains a SearXNG provider using `SEARXNG_URL` and `/search?format=json`. That provider is search-only; extraction is a separate backend. Hermes also supports stdio MCP. | `mcp_servers.cad_web`: `command`, `args`, `enabled: true`, timeout/connect_timeout in seconds; `supports_parallel_tool_calls: false`; add `cad_web` to an explicit `--toolsets` list |

Exact integration belongs in newly generated run configuration. Preserve existing native tools rather than changing a second factor in the comparison. In automatic runs, explicitly allow the two discovered MCP tools using that harness's existing permission mechanism. Cline uses its workspace `.cline` MCP settings as in the existing starter. For Hermes server key `cad_web`, discovery registers canonical toolset `mcp-cad_web` and alias `cad_web`. With the starter's explicit toolset list, append `,cad_web` when this optional MCP is enabled. `mcp_cad_web` is a tool-name prefix, not the toolset name; a generic `mcp` group does not enable it. This was checked against installed `tools/mcp_tool_registration.py`, `tools/registry.py`, `toolsets.py` and `model_tools.py`, and reproduced with inert registry entries without starting discovery or a transport. A config parse or direct MCP fixture does not establish that a particular model selected or used the new tools.

Primary versioned sources: OpenCode 1 [fetch](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/opencode/src/tool/webfetch.ts) and [search](https://github.com/anomalyco/opencode/blob/v1.19.6/packages/opencode/src/tool/websearch.ts); OpenCode 2 [fetch plugin](https://github.com/anomalyco/opencode/blob/v2.3.2/packages/core/src/tool/plugin/webfetch.ts), [search plugin](https://github.com/anomalyco/opencode/blob/v2.3.2/packages/core/src/tool/plugin/websearch.ts) and [provider registry](https://github.com/anomalyco/opencode/blob/v2.3.2/packages/core/src/websearch.ts); Crush [fetch](https://github.com/charmbracelet/crush/blob/v0.102.0/internal/agent/tools/fetch.go), [subagent search](https://github.com/charmbracelet/crush/blob/v0.102.0/internal/agent/tools/web_search.go) and [subagent fetch](https://github.com/charmbracelet/crush/blob/v0.102.0/internal/agent/tools/web_fetch.go); Hermes [SearXNG provider](https://github.com/NousResearch/hermes-agent/blob/v0.23.3/plugins/web/searxng/provider.py) and [MCP transport](https://github.com/NousResearch/hermes-agent/blob/v0.23.3/tools/mcp_tool.py). Cline findings were checked against the installed SDK/Core 0.2.1 package's `extensions/tools/presets.d.ts`, `extensions/tools/types.d.ts`, bundled implementation and `@cline/shared` model-tool declarations, then reproduced through its exported tool builders with inert executors.

## CPU/HTTP checks

The separate private fixture `web-adapter-http-fixture/check-web-tools.py` starts only this stdio adapter. On 23 November 2026 at 19:57:42 UTC it verified:

- omitted mode defaults to off, tools/list is empty, a fetch call is rejected, and no evidence/HTTP work is performed;
- initialize and tools/list expose the expected two tools when on;
- fetch-only exposes only `web_fetch`, retrieves real FreeCAD documentation even with a deliberately unavailable SearXNG address, and rejects search without contacting it;
- `--check` independently reports the expected real capabilities for off, fetch and search;
- the existing `http://127.0.0.1:8080` returns a real FreeCAD query with search results;
- HTTP 200 retrieval of the FreeCAD source README, `https://wiki.freecad.org/Spreadsheet_SetAlias` with its actual documentation title, and our public `dolmario/local-ai-cad-kit` README;
- every retained `.body` matches the SHA256 in its receipt.

`inspect-cline-tools.mjs` separately built SDK tool catalogs with inert executors: yolo omitted `fetch_web_content`, act and the generic default builder included it. It never created/started/sent a Cline session. A separate `inspect-hermes-toolsets.py` CPU fixture verified that the explicit Hermes toolset list must add `cad_web` or `mcp-cad_web` to select these server tools; `mcp_cad_web` and `mcp` do not do so. Versioned upstream HTTP source captures, including honest 404s from old source paths, were saved separately. No model, FreeCAD, GPU, ASR, render, browser-control session or local listener was started by these checks.

## Night-run task

Use `tasks/editable-enclosure-web.txt`; its entire baseline geometry brief is byte-identical to `tasks/editable-enclosure.txt`, followed only by the research/source-recording assignment. `tasks/editable-enclosure-web.scope.json` pins its baseline digest, complete v4 skill digests and comparison conditions. It is a reviewable scope record, not a runner and not permission to overlap GPU work.

The overnight run used Inkling 2 Mini through Cline Core and the b12649 ROCm build. It searched the web, fetched sources and made 29 CAD-code calls. It saved a native 120 mm enclosure plus STEP and STL files for the body and lid. A ROCm launch failure ended the run before the 140 mm exports, the manifest, the requested source journal and the skill-reuse exercise. The fetch tool retained source receipts.

The original 120 mm files passed independent checks. Changing the existing length parameter later produced a 140 mm version on the CPU. Both sizes are available with their export history and file checks in the companion material. The run also used a corrected image adapter and received help recovering its own FreeCAD session. It therefore leaves the individual effect of web access on CAD quality or completion time open. See [CAD-NEXT.md](CAD-NEXT.md) for the measured results.

The Windows starter check on 24 November also exercised the optional web tool from a fresh Cline text session. It retrieved the FreeCAD spreadsheet-alias page and saved a matching source receipt. A deterministic provider issued that tool call. In the earlier model run, Inkling itself selected the web actions.
