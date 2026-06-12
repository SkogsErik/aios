"""
frontmatter_util.py — Minimal YAML front-matter parser.

Replaces the external `frontmatter` / `python-frontmatter` dependency.
Supports the standard --- delimited YAML front-matter block in Markdown files.
"""

import yaml


def parse(text: str) -> tuple[dict, str]:
    """Parse a string with optional YAML front-matter.

    Returns (metadata_dict, content_string). If no front-matter is
    present, metadata_dict is empty and content_string is the full text.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break

    if end is None:
        return {}, text

    fm_block = "\n".join(lines[1:end])
    content = "\n".join(lines[end + 1:])
    meta = yaml.safe_load(fm_block) or {}
    return meta, content


def build(meta: dict, content: str) -> str:
    """Build a string with YAML front-matter prepended to content."""
    fm = yaml.dump(meta, default_flow_style=False, sort_keys=False).strip()
    return f"---\n{fm}\n---\n{content}"


def load(path: str) -> "Post":
    """Load a file and return a Post with .metadata and .content."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    meta, content = parse(text)
    return Post(meta, content)


class Post:
    """Thin object matching the `frontmatter.Post` interface.

    Supports construction as either:
      Post(metadata_dict, content_str)   — from _load_fm()
      Post(content_str, key=value, ...)  — from test helpers
    """
    def __init__(self, *args, **kwargs) -> None:
        if args and isinstance(args[0], dict):
            self.metadata = args[0]
            self.content = args[1] if len(args) > 1 else ""
        else:
            self.metadata = kwargs
            self.content = args[0] if args else ""


def dumps(post: "Post") -> str:
    """Serialize a Post object to a string with YAML front-matter."""
    return build(post.metadata, post.content)
