import re
import markdown
from html import unescape
from bs4 import BeautifulSoup


# -------------------------------------------------------
# TOC
# -------------------------------------------------------

def generate_toc():
    return """
<ac:structured-macro ac:name="toc">
  <ac:parameter ac:name="minLevel">1</ac:parameter>
  <ac:parameter ac:name="maxLevel">4</ac:parameter>
</ac:structured-macro>
"""


def inject_toc(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for p in soup.find_all("p"):
        if re.match(r"^\[\s*toc\s*\]$", p.get_text(strip=True), re.IGNORECASE):
            toc = BeautifulSoup(generate_toc(), "html.parser")
            p.replace_with(toc)

    return str(soup)


# -------------------------------------------------------
# Canonical function
# -------------------------------------------------------

def canonicalize_for_compare(html: str) -> list[str]:
    """
    Stable semantic normalization for Confluence drift.

    Fixes:
    - <p> echo AFTER <li> (edit-mode artifact)
    - <p> echo BEFORE <li>
    - prefix fragmentation
    - duplicate structural nodes
    """

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(True):
        tag.attrs.pop("data-responsive", None)
        tag.attrs.pop("data-responsive-wrapper", None)

    elements = list(
        soup.find_all(
            ["h1", "h2", "h3", "h4", "p", "li", "td", "th"],
            recursive=True
        )
    )

    def clean(t: str) -> str:
        return " ".join(t.split())

    cleaned = [
        (el.name, clean(el.get_text(" ", strip=True)))
        for el in elements
        if el.get_text(" ", strip=True)
    ]

    blocks = []
    seen = set()

    def is_dup(a, b):
        return a == b

    i = 0
    while i < len(cleaned):
        tag, text = cleaned[i]

        key = (tag, text)

        # ---------------------------------------------------
        # 1. skip exact duplicates
        # ---------------------------------------------------
        if key in seen:
            i += 1
            continue
        seen.add(key)

        # ---------------------------------------------------
        # 2. suppress <p> duplicates (BOTH directions)
        # ---------------------------------------------------
        if tag == "p":

            prev = cleaned[i - 1] if i > 0 else None
            nxt = cleaned[i + 1] if i + 1 < len(cleaned) else None

            # case A: p after li/td/th
            if prev and prev[0] in ("li", "td", "th") and prev[1] == text:
                i += 1
                continue

            # case B: p before li/td/th
            if nxt and nxt[0] in ("li", "td", "th") and nxt[1] == text:
                i += 1
                continue

            # case C: prefix fragment of next li
            if nxt and nxt[0] == "li":
                if nxt[1].startswith(text) and len(text) < len(nxt[1]):
                    i += 1
                    continue

        blocks.append(f"<{tag}>{text}</{tag}>")
        i += 1

    return blocks
        
# -------------------------------------------------------
# MARKDOWN → HTML
# -------------------------------------------------------

def md_to_html(md: str) -> str:
    return markdown.markdown(md, extensions=["tables", "fenced_code"])


# -------------------------------------------------------
# FIX EMPTY LIST ITEMS
# -------------------------------------------------------

def fix_empty_list_items(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for li in list(soup.find_all("li")):

        nested = li.find(["ul", "ol"])

        if not li.get_text(strip=True) and not nested:
            li.decompose()
            continue

        if nested and not li.get_text(strip=True):
            li.insert_after(nested)
            li.decompose()

    return str(soup)


# -------------------------------------------------------
# RESPONSIVE TABLES
# -------------------------------------------------------

def make_tables_responsive(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for table in soup.find_all("table"):
        table["style"] = "width:100%"
        table.attrs.pop("data-responsive", None)

    return str(soup)


# -------------------------------------------------------
# STABILIZE HTML (STRUCTURE ONLY - NO TEXT LOGIC)
# -------------------------------------------------------

def stabilize_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # ---------------------------------------------------
    # REMOVE WHITESPACE-ONLY TEXT NODES (SAFE)
    # ---------------------------------------------------
    for node in list(soup.find_all(string=True)):
        if not node.strip():
            node.extract()

    # ---------------------------------------------------
    # NORMALIZE TAGS / ATTRIBUTES
    # ---------------------------------------------------

    for tag in soup.find_all(True):

        for attr in [
            "ac:macro-id",
            "ac:schema-version",
            "ri:version-at-save",
            "data-responsive",
            "data-responsive-wrapper",
        ]:
            tag.attrs.pop(attr, None)

        style = tag.get("style")

        if style:
            style = re.sub(r"\s+", "", style)
            style = style.replace("100.0%", "100%")
            style = style.replace("100.0px", "100px")
            style = style.replace(";;", ";").rstrip(";")

            parts = sorted([p for p in style.split(";") if p])
            tag["style"] = ";".join(parts)

    # ---------------------------------------------------
    # REMOVE EMPTY PARAGRAPHS
    # ---------------------------------------------------

    for p in list(soup.find_all("p")):
        if not p.get_text(strip=True) and not p.find():
            p.decompose()

    # ---------------------------------------------------
    # IMPORTANT: DO NOT TOUCH TEXT CONTENT ANYMORE
    # ---------------------------------------------------
    # (this was the bug causing paragraph merging)

    return str(soup)


# -------------------------------------------------------
# STORAGE FORMAT
# -------------------------------------------------------

def html_to_storage(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.decode(formatter="minimal")


# -------------------------------------------------------
# NORMALIZE FOR DIFFING (SAFE ONLY)
# -------------------------------------------------------

def normalize_html(html: str) -> str:
    return "\n".join(canonicalize_for_compare(html))


def normalize_block_structure(html: str) -> str:
    """
    Ensures block separation inside table cells and paragraphs
    BEFORE Confluence serialization.
    """

    soup = BeautifulSoup(html, "html.parser")

    # ---------------------------------------------------
    # FIX: split merged <p> inside <td>
    # ---------------------------------------------------

    for td in soup.find_all("td"):
        new_content = []

        for child in list(td.children):

            if child.name == "p":
                text = child.get_text(" ", strip=True)

                if text:
                    new_content.append(f"<p>{text}</p>")

            elif child.name is None:
                # skip whitespace-only text nodes
                continue

            else:
                new_content.append(str(child))

        if new_content:
            td.clear()
            td.append(BeautifulSoup("".join(new_content), "html.parser"))

    return str(soup)