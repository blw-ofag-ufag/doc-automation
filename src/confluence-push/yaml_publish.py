import sys
import os
import re
import json
import yaml
import hashlib
import requests
import argparse
import unicodedata
import difflib


from pathlib import Path
from html import escape
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from confluence_storage import (
    md_to_html,
    inject_toc,
    fix_empty_list_items,
    make_tables_responsive,
    stabilize_html,
    html_to_storage,
    normalize_html, 
    normalize_block_structure
)

from svg_converter import svg_to_png


# -------------------------------------------------------
# ENV
# -------------------------------------------------------

load_dotenv(
    dotenv_path=os.path.expanduser(
        "./.env"
    )
)

BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
AUTH_EMAIL = os.getenv("CONFLUENCE_EMAIL")
AUTH_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

STATE_FILE = "./build/confluence-push/.state.json"

if not BASE_URL:
    raise ValueError(
        "❌ CONFLUENCE_BASE_URL not set"
    )

if not AUTH_EMAIL:
    raise ValueError(
        "❌ CONFLUENCE_EMAIL not set"
    )

if not AUTH_TOKEN:
    raise ValueError(
        "❌ CONFLUENCE_API_TOKEN not set"
    )


# -------------------------------------------------------
# AUTH
# -------------------------------------------------------

def auth():
    return (AUTH_EMAIL, AUTH_TOKEN)


# -------------------------------------------------------
# HASH
# -------------------------------------------------------

def file_hash(path):

    with open(path, "rb") as f:
        return hashlib.md5(
            f.read()
        ).hexdigest()


def content_hash(text: str) -> str:

    return hashlib.md5(
        text.encode("utf-8")
    ).hexdigest()


# -------------------------------------------------------
# STATE
# -------------------------------------------------------

def load_state():

    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read().strip()

            if not content:
                return {}

            return json.loads(content)

    except json.JSONDecodeError:

        print(
            "⚠️ State file corrupted — resetting"
        )

        return {}


def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            indent=2
        )


# -------------------------------------------------------
# DIFF
# -------------------------------------------------------

def show_diff(old: str, new: str, context=3):
    """
    Stable structural diff for Confluence storage HTML.

    Key idea:
    We DO NOT diff HTML.
    We diff normalized BLOCKS:
      - p
      - li
      - h1-h4
      - td/th

    Each block becomes a single semantic unit.
    """

    def html_to_blocks(html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")

        # remove only non-semantic noise
        for tag in soup.find_all(True):
            tag.attrs.pop("data-responsive", None)
            tag.attrs.pop("data-responsive-wrapper", None)

        blocks = []

        # IMPORTANT: enforce deterministic order (document order only)
        for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th"], recursive=True):

            # skip empty containers
            text = el.get_text(" ", strip=True)

            if not text:
                continue

            # normalize whitespace INSIDE block only (safe)
            text = " ".join(text.split())

            blocks.append(f"<{el.name}>{text}</{el.name}>")

        return blocks

    old_blocks = html_to_blocks(old)
    new_blocks = html_to_blocks(new)

    diff = difflib.unified_diff(
        old_blocks,
        new_blocks,
        fromfile="confluence",
        tofile="local",
        lineterm="",
        n=context
    )

    has_changes = False

    for line in diff:
        has_changes = True

        if line.startswith("+") and not line.startswith("+++"):
            print(f"\033[32m{line}\033[0m")

        elif line.startswith("-") and not line.startswith("---"):
            print(f"\033[31m{line}\033[0m")

        else:
            print(line)

    if not has_changes:
        print("✔ No differences")

# -------------------------------------------------------
# INDENTATION
# -------------------------------------------------------

def normalize_indentation(md: str) -> str:

    lines = md.splitlines()

    fixed = []

    for line in lines:

        if not line.strip():
            fixed.append(line)
            continue

        # headings
        if re.match(
            r"^\s{0,3}#{1,6}\s",
            line
        ):
            fixed.append(line.lstrip())
            continue

        spaces = len(line) - len(
            line.lstrip(" ")
        )

        if spaces >= 2:

            level = spaces // 2

            line = (
                "    " * level
                + line.lstrip()
            )

        fixed.append(line)

    return "\n".join(fixed)


# -------------------------------------------------------
# CUSTOM BLOCKS
# -------------------------------------------------------

def convert_custom_blocks(md: str) -> str:

    blocks = {
        "INFO": "info",
        "WARNING": "warning"
    }

    for tag, macro in blocks.items():

        pattern = re.compile(
            rf"\[{tag}\]\s*(.*?)\s*\[/{tag}\]",
            re.DOTALL | re.IGNORECASE
        )

        def repl(match):

            content = escape(
                match.group(1).strip()
            )

            return (
                f'<ac:structured-macro '
                f'ac:name="{macro}">'
                f'<ac:rich-text-body>'
                f'<p>{content}</p>'
                f'</ac:rich-text-body>'
                f'</ac:structured-macro>'
            )

        md = pattern.sub(repl, md)

    return md


# -------------------------------------------------------
# ATTACHMENTS
# -------------------------------------------------------

def extract_used_attachments(
    md,
    attachments
):

    used = set()

    for name in attachments.keys():

        if re.search(
            rf"@attach\s+{re.escape(name)}(\s*\|.*)?",
            md
        ):
            used.add(name)

        if re.search(
            rf"!\[{re.escape(name)}\]\(",
            md
        ):
            used.add(name)

    return used


def normalize_filename(name: str) -> str:

    name = unicodedata.normalize(
        "NFKD",
        name
    ).encode(
        "ascii",
        "ignore"
    ).decode()

    name = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        name
    )

    name = re.sub(
        r"_+",
        "_",
        name
    )

    return name


def get_confluence_filename(
    name,
    path
):

    ext = os.path.splitext(path)[1].lower()

    if ext == ".svg":

        path = svg_to_png(path)

        ext = ".png"

    h = file_hash(path)

    return f"{name}__{h[:12]}{ext}"


# -------------------------------------------------------
# CONFLUENCE API
# -------------------------------------------------------

def get_page(page_id):

    url = (
        f"{BASE_URL}"
        f"/rest/api/content/{page_id}"
        f"?expand=body.storage,version,title"
    )

    r = requests.get(
        url,
        auth=auth(),
        timeout=30
    )

    r.raise_for_status()

    return r.json()


def update_page(
    page_id,
    title,
    version,
    html
):

    url = (
        f"{BASE_URL}"
        f"/rest/api/content/{page_id}"
    )

    payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "version": {
            "number": version
        },
        "body": {
            "storage": {
                "value": html,
                "representation": "storage"
            }
        }
    }

    r = requests.put(
        url,
        json=payload,
        auth=auth(),
        timeout=30
    )

    r.raise_for_status()


def get_attachments(page_id):

    url = (
        f"{BASE_URL}"
        f"/rest/api/content/{page_id}"
        f"/child/attachment"
    )

    r = requests.get(
        url,
        auth=auth(),
        timeout=30
    )

    r.raise_for_status()

    return r.json().get(
        "results",
        []
    )


# -------------------------------------------------------
# ATTACHMENT UPLOAD
# -------------------------------------------------------

def upload_attachment_if_changed(
    base_url,
    auth_tuple,
    page_id,
    file_path,
    filename=None
):

    file_path = Path(file_path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    original_filename = file_path.name

    filename = (
        filename
        or normalize_filename(original_filename)
    )

    print(
        f"📎 {original_filename} → {filename}"
    )

    existing = get_attachments(page_id)

    existing_names = {
        a["title"]
        for a in existing
    }

    if filename in existing_names:

        print(
            "   → unchanged (already exists)"
        )

        return None

    print("   → uploading")

    url = (
        f"{base_url}"
        f"/rest/api/content/{page_id}"
        f"/child/attachment"
    )

    with open(file_path, "rb") as f:

        files = {
            "file": (
                filename,
                f
            )
        }

        headers = {
            "X-Atlassian-Token": "no-check"
        }

        r = requests.post(
            url,
            headers=headers,
            files=files,
            auth=auth_tuple
        )

    if not r.ok:

        print("❌ Upload failed")
        print("Status:", r.status_code)
        print("Response:", r.text)

    r.raise_for_status()

    return r.json()


# -------------------------------------------------------
# MARKDOWN PROCESSING
# -------------------------------------------------------

def process_markdown(
    file_path,
    attachments,
    page_id,
    dry_run,
    config_dir
):

    file_path = os.path.abspath(
        os.path.join(
            config_dir,
            file_path
        )
    )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        md = f.read()

    md = normalize_indentation(md)

    md = convert_custom_blocks(md)

    used = extract_used_attachments(
        md,
        attachments
    )

    for name, meta in attachments.items():

        if isinstance(meta, str):

            raw_path = meta
            yaml_caption = None

        else:

            raw_path = meta.get("path")
            yaml_caption = meta.get("caption")

        path = os.path.abspath(
            os.path.join(
                config_dir,
                raw_path
            )
        )

        if name not in used:
            continue

        if not os.path.exists(path):

            print(
                f"⚠️ missing file: {path}"
            )

            continue

        confluence_filename = (
            get_confluence_filename(
                name,
                path
            )
        )

        upload_attachment_if_changed(
            BASE_URL,
            auth(),
            page_id,
            path,
            confluence_filename
        )

        inline_match = re.search(
            rf"@attach\s+{re.escape(name)}\s*\|\s*(.+)",
            md
        )

        caption = (
            inline_match.group(1).strip()
            if inline_match
            else yaml_caption
        )

        replacement = (
            f'<p>'
            f'<ac:image ac:width="100%">'
            f'<ri:attachment '
            f'ri:filename="{confluence_filename}"/>'
            f'</ac:image>'
            f'</p>'
        )

        if caption:

            replacement += (
                f'<p><em>'
                f'{escape(caption)}'
                f'</em></p>'
            )

        md = re.sub(
            rf"@attach\s+{re.escape(name)}(\s*\|.*)?",
            replacement,
            md
        )

    html = md_to_html(md)
    html = normalize_block_structure(html)
    html = inject_toc(html)

    html = fix_empty_list_items(html)

    html = make_tables_responsive(html)

    html = stabilize_html(html)

    html = html_to_storage(html)

    return html.strip()


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("config")

    parser.add_argument(
        "--dry-run",
        "-dr",
        action="store_true"
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true"
    )

    args = parser.parse_args()

    config_path = os.path.abspath(
        args.config
    )

    config_dir = os.path.dirname(
        config_path
    )

    with open(
        config_path,
        "r",
        encoding="utf-8"
    ) as f:

        cfg = yaml.safe_load(f)

    # -------------------------------------------------------
    # CONFIG VALIDATION (IMPORTANT SAFETY CHECK)
    # -------------------------------------------------------

    seen_ids = set()

    for page in cfg.get("pages", []):
        page_id = str(page.get("id"))

        if page_id in seen_ids:
            raise ValueError(
                f"❌ Duplicate page id in config: {page_id}"
            )

    seen_ids.add(page_id)

    state = load_state()

    for page in cfg["pages"]:

        page_id = str(page["id"])

        file_path = page["file"]

        attachments = page.get(
            "attachments",
            {}
        )

        title = page.get("name")

        print(f"\n🚀 Page {page_id}")

        # -------------------------------------------------------
        # LOAD REMOTE PAGE
        # -------------------------------------------------------

        data = get_page(page_id)

        version = data["version"]["number"]

        title = title or data["title"]

        remote_html = data[
            "body"
        ]["storage"]["value"]

        # -------------------------------------------------------
        # BUILD LOCAL HTML
        # -------------------------------------------------------

        new_html = process_markdown(
            file_path,
            attachments,
            page_id,
            args.dry_run,
            config_dir
        )

        # -------------------------------------------------------
        # NORMALIZE FOR COMPARISON
        # -------------------------------------------------------

        remote_canon = normalize_html(
            remote_html
        )

        new_canon = normalize_html(
            new_html
        )

        new_hash = content_hash(
            new_canon
        )

        # -------------------------------------------------------
        # DRY RUN
        # -------------------------------------------------------

        if args.dry_run:

            print(
                "🧪 DRY RUN — showing semantic diff:\n"
            )

            show_diff(
                remote_canon,
                new_canon
            )

            continue

        # -------------------------------------------------------
        # CONFLICT DETECTION
        # -------------------------------------------------------

        if remote_canon != new_canon:

            print(
                "⚠️ Page content differs"
            )


            # SHOW DIFF BEFORE ANY DECISION
            print("🧪 Showing diff:\n")

            show_diff(remote_canon, new_canon)

            print("\n---\n")

            if not args.force:

                user_input = input(
                    '→ manual resolution required: '
                    'type "q" to quit or '
                    '"FORCE" to overwrite: '
                ).strip()

                if user_input.lower() == "q":

                    print("❌ Aborted")

                    sys.exit(1)

                if user_input != "FORCE":

                    print(
                        "❌ Invalid input"
                    )

                    sys.exit(1)

                print(
                    "⚠️ Forcing update..."
                )

        else:

            print(
                "✔ No content conflict detected"
            )

        # -------------------------------------------------------
        # UPDATE PAGE
        # -------------------------------------------------------

        update_page(
            page_id,
            title,
            version + 1,
            new_html
        )

        print("✅ updated")

        # -------------------------------------------------------
        # SAVE STATE
        # -------------------------------------------------------

        state[page_id] = {
            "hash": new_hash
        }

        save_state(state)


if __name__ == "__main__":
    main()