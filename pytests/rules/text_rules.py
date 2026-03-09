"""Reusable text/length constraints and regex patterns."""

SHORT_NAME_MAX = 50
OVERVIEW_MIN = 200
OVERVIEW_MAX = 500
LONG_TEXT_MAX = 2000
MISSION_MAX = 500

COUNTRIES_LIST_PATTERN = r"^([A-Za-z\s]+)(,\s*[A-Za-z\s]+)*$"
ENTITY_LIST_PATTERN = r"^[\w\s&.,\-/]+(,\s*[\w\s&.,\-/]+)*$"
INVESTOR_LIST_PATTERN = r"^[\w\s&.,\-\(\)]+(,\s*[\w\s&.,\-\(\)]+)*$"
