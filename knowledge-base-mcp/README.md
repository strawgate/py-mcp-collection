# Knowledge Base MCP

An MCP Server for creating knowledge bases and searching them!

## Features

- **Multiple Vector Store Backends**: Works with DuckDB and Elasticsearch.
- **Website Ingestion**: Load and crawl documentation or websites into a knowledge base.
- **Git Repository Ingestion**: Load and ingest a Git repository into a knowledge base.
- **Directory Ingestion**: Load and ingest a directory into a knowledge base.
- **Semantic Search**: Query across one or more knowledge bases using embeddings and reranking.
- **Knowledge Base Management**: List, remove, or clear knowledge bases.

## Usage

### Command-Line Interface

The CLI supports both DuckDB (in-memory or persistent) and Elasticsearch as vector store backends.

#### DuckDB (Persistent)

To run the server with a persistent DuckDB store, which will save your knowledge bases to disk:

```bash
uv run knowledge_base_mcp duckdb persistent --docs-db-dir ./storage --docs-db-name documents.duckdb --code-db-dir ./storage --code-db-name code.duckdb run
```

- `--docs-db-dir`: Directory to store document knowledge base. Defaults to `./storage`.
- `--docs-db-name`: Filename for the document knowledge base. Defaults to `documents.duckdb`.
- `--code-db-dir`: Directory to store code knowledge base. Defaults to `./storage`.
- `--code-db-name`: Filename for the code knowledge base. Defaults to `code.duckdb`.

#### DuckDB (In-Memory)

To run the server with an in-memory DuckDB store (data will not be persisted after the server stops):

```bash
uv run knowledge_base_mcp duckdb memory run
```

#### Elasticsearch

To run the server with Elasticsearch as the backend, ensure you have an Elasticsearch instance running and accessible.

```bash
uv run knowledge_base_mcp elasticsearch --url http://localhost:9200 --index-docs-vectors kbmcp-docs-vectors --index-docs-kv kbmcp-docs-kv --index-code-vectors kbmcp-code-vectors --index-code-kv kbmcp-code-kv run
```

You can also set Elasticsearch options via environment variables:
- `ES_URL`: Elasticsearch instance URL (e.g., `http://localhost:9200`).
- `ES_INDEX_DOCS_VECTORS`: Index name for document vectors. Defaults to `kbmcp-docs-vectors`.
- `ES_INDEX_DOCS_KV`: Index name for document key-value store. Defaults to `kbmcp-docs-kv`.
- `ES_INDEX_CODE_VECTORS`: Index name for code vectors. Defaults to `kbmcp-code-vectors`.
- `ES_INDEX_CODE_KV`: Index name for code key-value store. Defaults to `kbmcp-code-kv`.
- `ES_USERNAME`: Username for Elasticsearch authentication.
- `ES_PASSWORD`: Password for Elasticsearch authentication.
- `ES_API_KEY`: API Key for Elasticsearch authentication.

### Main Server Tools/Endpoints

When running, the MCP server exposes the following tools:

#### Ingestion Tools (from `IngestServer`)

- **load_website**: Create a new knowledge base from a website by crawling seed URLs. If the knowledge base already exists, it will be replaced.
  - Parameters: `knowledge_base` (name for the new KB), `seed_urls` (list of URLs to start crawling), `url_exclusions` (optional list of URLs to exclude), `max_pages` (optional maximum number of pages to crawl).
- **load_directory**: Create a new knowledge base from files within a local directory.
  - Parameters: `knowledge_base` (name for the new KB), `path` (path to the directory), `exclude` (optional file path globs to exclude), `extensions` (optional list of file extensions to include, defaults to Markdown and AsciiDoc), `recursive` (optional, whether to recursively gather files, defaults to True).
- **load_git_repository**: Create a new knowledge base from a Git repository by cloning it and ingesting its contents.
  - Parameters: `knowledge_base` (name for the new KB), `repository_url` (URL of the Git repository), `branch` (branch to clone), `path` (path within the repository to ingest), `exclude` (optional file path globs to exclude), `extensions` (optional list of file extensions to include, defaults to Markdown and AsciiDoc).

#### Search Tools (from `KnowledgeBaseSearchServer`)

- **query**: Search across one or more knowledge bases using a natural language question.
  - Parameters: `query` (the plain language query string), `knowledge_bases` (optional list of knowledge base names to restrict the search to; searches all if not provided).
- **get_document**: Retrieve a specific document from a knowledge base by its title.
  - Parameters: `knowledge_base` (the name of the knowledge base), `title` (the title of the document).

#### Management Tools (from `KnowledgeBaseManagementServer`)

- **get_knowledge_bases**: List all available knowledge bases and their document counts.
- **delete_knowledge_base**: Remove a specific knowledge base by its name.
  - Parameters: `knowledge_base` (the name of the knowledge base to delete).
- **delete_all_knowledge_bases**: Remove all knowledge bases from the vector store.
- **get_knowledge_base_stats**: Get detailed statistics for a specific knowledge base.
  - Parameters: `knowledge_base` (the name of the knowledge base).

## VS Code McpServer Usage

1. Open the command palette (Ctrl+Shift+P or Cmd+Shift+P).
2. Type "Settings" and select "Preferences: Open User Settings (JSON)".
3. Add the following MCP Server configuration:

```json
{
    "mcp": {
        "servers": {
            "Knowledge Base": {
                "command": "uvx",
                "args": [
                    "knowledge_base_mcp",
                    "duckdb",
                    "persistent",
                    "run"
                ]
            }
        }
    }
}
```

## Roo Code


```json
{
    "mcpServers": {
      "Knowledge Base": {
          "command": "uvx",
          "args": [
              "git+https://github.com/strawgate/py-mcp-collection.git#subdirectory=knowledge_base_mcp",
              "duckdb",
              "persistent",
              "run"
          ]
      }
    }
}
```

## License

See [LICENSE](LICENSE).