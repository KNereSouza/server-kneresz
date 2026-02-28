import bleach

ALLOWED_TAGS = [
    "a", "abbr", "b", "blockquote", "br", "code", "del",
    "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i",
    "img", "li", "ol", "p", "pre", "strong", "sub", "sup",
    "table", "tbody", "td", "th", "thead", "tr", "ul",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
}


def sanitize_markdown(body: str) -> str:
    return bleach.clean(
        body,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
