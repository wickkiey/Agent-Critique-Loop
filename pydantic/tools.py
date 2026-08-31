"""Real tools: free web search (DuckDuckGo, no API key) and local project file search."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

from ddgs import DDGS

SEARCH_ROOT = Path(__file__).parent  # confine file_search to this project's own folder
SEARCH_EXTENSIONS = ("*.py", "*.md", "*.txt", "*.json")
MAX_RESULTS = 5
WEB_SEARCH_TIMEOUT_SECONDS = 15


def web_search(query: str) -> str:
    """Search the web via DuckDuckGo (free, no API key) and return the top results.

    Bounded by a hard timeout so DuckDuckGo rate-limiting can't stall the whole critique loop.
    """
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(lambda: list(DDGS(timeout=10).text(query, max_results=MAX_RESULTS)))
    try:
        results = future.result(timeout=WEB_SEARCH_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        return f"Web search timed out for '{query}'."
    except Exception as exc:
        return f"Web search failed: {exc}"
    finally:
        executor.shutdown(wait=False)  # don't block on a still-running (timed-out) search thread
    if not results:
        return f"No web results found for '{query}'."
    return "\n".join(f"- {r['title']}: {r['body']} ({r['href']})" for r in results)


def file_search(query: str) -> str:
    """Search text files in this project's folder for lines containing the query."""
    matches: list[str] = []
    for pattern in SEARCH_EXTENSIONS:
        for path in SEARCH_ROOT.rglob(pattern):
            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, start=1):
                if query.lower() in line.lower():
                    matches.append(f"{path.relative_to(SEARCH_ROOT)}:{lineno}: {line.strip()}")
                    if len(matches) >= MAX_RESULTS:
                        break
            if len(matches) >= MAX_RESULTS:
                break
        if len(matches) >= MAX_RESULTS:
            break
    if not matches:
        return f"No file matches found for '{query}'."
    return "\n".join(matches)

