import re
from urllib.parse import quote_plus

VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def extract_variables(template: str) -> list[str]:
    return list(dict.fromkeys(VARIABLE_PATTERN.findall(template)))


def resolve_template(template: str, variables: dict[str, str]) -> tuple[str, list[str]]:
    """Replace {{var}} placeholders. Returns (resolved_text, missing_vars)."""
    missing: list[str] = []

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in variables and variables[key]:
            return variables[key]
        missing.append(key)
        return match.group(0)

    resolved = VARIABLE_PATTERN.sub(replacer, template)
    # de-dupe missing while preserving order
    missing = list(dict.fromkeys(missing))
    return resolved, missing


def google_search_url(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}"
