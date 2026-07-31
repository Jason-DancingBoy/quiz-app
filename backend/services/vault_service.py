import os

from backend.logger import get_logger

logger = get_logger(__name__)


def scan_vault_files(vault_dir: str) -> list[tuple[str, str]]:
    """Recursively scan a vault directory, return [(filename, content), ...] for .md files."""
    files = []
    if not os.path.isdir(vault_dir):
        logger.warning("Vault directory not found: %s", vault_dir)
        return files

    for root, _, filenames in os.walk(vault_dir):
        for fname in filenames:
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(root, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.strip():
                    files.append((fname, content))
            except Exception:
                logger.warning("Failed to read vault file: %s", filepath)

    logger.info("Vault scan complete: %d .md files found in %s", len(files), vault_dir)
    return files


def build_vault_content(files: list[tuple[str, str]]) -> str:
    """Concatenate vault file contents into a single document string."""
    sections = []
    for fname, content in files:
        sections.append(f"# {fname}\n\n{content}")
    return "\n\n---\n\n".join(sections)
