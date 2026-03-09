"""Reusable URL and domain patterns."""

LOGO_URL_PATTERN = r"^https?://.*\.(?:png|jpg|jpeg|svg|webp)(?:\?.*)?$"
WEBSITE_URL_PATTERN = r"^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$"
LINKEDIN_COMPANY_PATTERN = r"^https?://(www\.)?linkedin\.com/company/[A-Za-z0-9_\-]+/?$"
TWITTER_X_PATTERN = r"^https?://(twitter\.com|x\.com)/[A-Za-z0-9_]{1,30}/?$"
FACEBOOK_PAGE_PATTERN = r"^https?://(www\.)?facebook\.com/[A-Za-z0-9_.\-]+/?$"
INSTAGRAM_PAGE_PATTERN = r"^https?://(www\.)?instagram\.com/[A-Za-z0-9_.\-]+/?$"
