from urllib.parse import urlparse, unquote, urljoin
import os


def safe_urljoin(base: str, url: str) -> str:
    try:
        if base is None:
            base = ""
        elif not isinstance(base, str):
            base = str(base)

        if url is None:
            url = ""
        elif not isinstance(url, str):
            url = str(url)

        if not base:
            return url
        if not url:
            return base

        return urljoin(base, url)
    except Exception as e:
        print(f"Error during operation urljoin: {str(e)}")
        return ""


def url_to_path(url: str) -> str:
    parsed = urlparse(url)
    path = unquote(parsed.path)

    while path.startswith("//"):
        path = path[1:]

    netloc = parsed.netloc.lower()

    # relative path
    if netloc == ".":
        if path.startswith("/"):
            path = path[1:]
        if not path:
            return "."
        if not (path.startswith("./") or path.startswith("../")):
            return f"./{path}"
        return path
    if not netloc and not path.startswith("/"):
        if path.startswith("./") or path.startswith("../"):
            return path
        return f"./{path}" if path else "."

    # localhost
    if not netloc or netloc == "localhost":
        if (
            os.name == "nt"
            and path.startswith("/")
            and len(path) > 2
            and path[2] == ":"
        ):
            # /C:/Users/... -> C:/Users/...
            path = path[1:]
        return path
