import bleach
from bleach.linkifier import Linker

ALLOWED_TAGS = [
    "a", "abbr", "b", "blockquote", "br", "code", "del",
    "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i",
    "img", "li", "ol", "p", "pre", "strong", "sub", "sup",
    "table", "tbody", "td", "th", "thead", "tr", "ul",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title"],
}


def _set_link_safety(attrs: dict, new: bool = False) -> dict:
    attrs[(None, "target")] = "_blank"
    attrs[(None, "rel")] = "noopener noreferrer"
    return attrs


def sanitize_markdown(body: str) -> str:
    cleaned = bleach.clean(
        body,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    linker = Linker(callbacks=[_set_link_safety], skip_tags=["pre", "code"])
    return linker.linkify(cleaned)
