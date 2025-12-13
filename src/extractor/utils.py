from urllib.parse import urlparse, unquote, urljoin
import os


def safe_urljoin(base: str | None, url: str | None) -> str:
    # safe wrap around urljoin (processes unexcepted variants)
    base = "" if base is None else str(base)
    url = "" if url is None else str(url)
    if not base:
        return url
    if not url:
        return base
    try:
        return urljoin(base, url)
    except Exception as e:
        print(f"safe_urljoin error: {e}")
        return ""


def url_to_path(url: str) -> str:
    # transform scheme part to file system path (for future parsing and extracting)
    parsed = urlparse(url)
    path = unquote(parsed.path or "")  # if not parsed.path return None (not "")

    # strip exstra slaches
    while path.startswith("//"):
        path = path[1:]

    netloc = (parsed.netloc or "").lower()

    # relative pathes "file://./x"
    if netloc == ".":
        p = path.lstrip("/")
        if not p:
            return "."
        if p.startswith(("./", "../")):
            return p
        return f"./{p}"

    # relative like "file:./x"
    if not netloc and not path.startswith("/"):
        if path.startswith(("./", "../")):
            return path
        return f"./{path}" if path else "."

    # localhost
    if not netloc or netloc == "localhost":
        # Windows: /C:/... -> C:/...
        if (
            os.name == "nt"
            and path.startswith("/")
            and len(path) > 2
            and path[2] == ":"
        ):
            return path[1:]
        return path

    return f"{netloc}{path}"
