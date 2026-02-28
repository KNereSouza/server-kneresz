from slugify import slugify


def generate_slug(title: str) -> str:
    return slugify(title, max_length=200)
