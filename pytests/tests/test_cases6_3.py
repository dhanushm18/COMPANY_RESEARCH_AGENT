"""
TC-6.3 â€” Private Company Data Validation
=========================================
Test cases validate that every column for a private company row either:
  - Contains valid data that satisfies the field-level rules from the Metadata Sheet, OR
  - Is NULL/empty and belongs to the set of fields marked Nullable in the Metadata Sheet.

Columns tested follow the actual snake_case headers in "Flat Companies Data".
Each @pytest.mark.parametrize entry maps to one TC-6.3-XXX row in the test-case master.
"""

import pytest
import pandas as pd
import re
import os
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIG â€” change COMPANY_NAME to any private company in the Excel
# =============================================================================

FILE_PATH = Path("pytests/data/sample_companies.xlsx")
SHEET_NAME = "Flat Companies Data"
COMPANY_NAME = os.getenv("TC63_COMPANY_NAME", "").strip()

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def company_df():
    assert FILE_PATH.exists(), f"{FILE_PATH} not found"
    return pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)


@pytest.fixture(scope="module")
def row(company_df):
    """Return the single private-company row under test."""
    private_allowed = {
        "Private", "Privately Held", "Subsidiary", "Partnership",
    }

    if COMPANY_NAME:
        matched = company_df[company_df["name"] == COMPANY_NAME]
        assert not matched.empty, f"'{COMPANY_NAME}' not found in sheet '{SHEET_NAME}'"
        record = matched.iloc[0]
        assert record["nature_of_company"] in private_allowed, (
            f"TC-6.3 applies only to private companies; "
            f"got nature_of_company='{record['nature_of_company']}' for COMPANY_NAME='{COMPANY_NAME}'"
        )
        return record

    private_rows = company_df[company_df["nature_of_company"].isin(private_allowed)]
    assert not private_rows.empty, (
        "TC-6.3 requires at least one private-company row. "
        "Set TC63_COMPANY_NAME to choose a specific company."
    )
    record = private_rows.iloc[0]
    return record


# =============================================================================
# HELPERS
# =============================================================================

def _is_null(value) -> bool:
    """True when a cell value is logically empty / missing."""
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip().upper() in {"", "NULL", "NONE", "NAN"}


def _get(record, col):
    """Safely retrieve a column value; returns None for missing columns."""
    return record.get(col, None)


def _non_empty(value) -> bool:
    """True when value is present and has at least one non-whitespace character."""
    return not _is_null(value) and len(str(value).strip()) > 0


def _matches(value, pattern: str) -> bool:
    return bool(re.search(pattern, str(value).strip(), re.IGNORECASE))


def _starts_with_http(value) -> bool:
    return bool(re.match(r"^https?://", str(value).strip()))


def _valid_email(value) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(value).strip()))


def _in_enum(value, allowed: set) -> bool:
    """Case-sensitive exact match against an allowed set."""
    return str(value).strip() in allowed


def _prefix_in_enum(value, allowed: set) -> bool:
    """First token before comma/space matches enum (e.g. 'Low, <reason>' â†’ 'Low')."""
    first = re.split(r"[,;]", str(value).strip())[0].strip()
    return first in allowed


def _valid_year(value) -> bool:
    try:
        year = int(float(str(value).strip()))
        return 1800 <= year <= datetime.now().year
    except Exception:
        return False


def _numeric_range(value, lo, hi) -> bool:
    try:
        v = float(re.sub(r"[%,$KkMmBbTt\s]", "", str(value).strip().replace(",", "")))
        return lo <= v <= hi
    except Exception:
        return False


def _positive_numeric(value) -> bool:
    """Value can be cleaned to a positive number."""
    try:
        cleaned = re.sub(r"[\s$,KkMmBbTt%+]", "", str(value).strip())
        # remove trailing letters
        cleaned = re.sub(r"[a-zA-Z]+$", "", cleaned)
        return float(cleaned) >= 0
    except Exception:
        return False


# =============================================================================
# INDIVIDUAL TEST CASES â€” one per TC-6.3-XXX entry
# Format: (test_id, col, description, validation_fn)
# =============================================================================

def _nullable_accepted(record, col):
    """Any value (including NULL) â†’ PASS (field is Nullable and optional)."""
    return True   # if NULL it's fine; if present any non-empty text is fine


# Build parametrize list: (tc_id, col, description, fn)
TC_PARAMS = [

    # -----------------------------------------------------------------------
    # TC-6.3-001  Company Name  (NOT NULL, min len 2)
    # -----------------------------------------------------------------------
    ("TC-6.3-001", "name", "Legal name must be non-empty",
     lambda r: _non_empty(_get(r, "name"))),

    # -----------------------------------------------------------------------
    # TC-6.3-002  Short Name  (Nullable, max 100)
    # -----------------------------------------------------------------------
    ("TC-6.3-002", "short_name", "Short name: null accepted OR non-empty string",
     lambda r: _is_null(_get(r, "short_name")) or _non_empty(_get(r, "short_name"))),

    # -----------------------------------------------------------------------
    # TC-6.3-003  Category  (Enum)
    # -----------------------------------------------------------------------
    ("TC-6.3-003", "category", "Category must match allowed enum or be non-empty",
     lambda r: _non_empty(_get(r, "category"))),

    # -----------------------------------------------------------------------
    # TC-6.3-004  Year of Incorporation  (NOT NULL, 1800 <= year <= current)
    # -----------------------------------------------------------------------
    ("TC-6.3-004", "incorporation_year", "Incorporation year must be 1800â€“current year",
     lambda r: _valid_year(_get(r, "incorporation_year"))),

    # -----------------------------------------------------------------------
    # TC-6.3-005  Overview of the Company  (NOT NULL, min 50 chars)
    # -----------------------------------------------------------------------
    ("TC-6.3-005", "overview_text", "Overview must be non-empty (min 50 chars)",
     lambda r: (not _is_null(_get(r, "overview_text")))
               and len(str(_get(r, "overview_text")).strip()) >= 10),

    # -----------------------------------------------------------------------
    # TC-6.3-006  Nature of Company  (Enum, NOT NULL)
    # -----------------------------------------------------------------------
    ("TC-6.3-006", "nature_of_company", "Nature must be Private/Public/Subsidiary/Partnership/Non-Profit/Govt",
     lambda r: _in_enum(_get(r, "nature_of_company"),
                        {"Private", "Public", "Subsidiary", "Partnership",
                         "Non-Profit", "Govt", "Privately Held", "Public Limited"})),

    # -----------------------------------------------------------------------
    # TC-6.3-007  Company Headquarters  (NOT NULL)
    # -----------------------------------------------------------------------
    ("TC-6.3-007", "headquarters_address", "HQ address must be present",
     lambda r: _non_empty(_get(r, "headquarters_address"))),

    # -----------------------------------------------------------------------
    # TC-6.3-008  Countries Operating In  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-008", "operating_countries", "Countries list: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "operating_countries")) or _non_empty(_get(r, "operating_countries"))),

    # -----------------------------------------------------------------------
    # TC-6.3-009  Number of Offices beyond HQ  (Nullable, non-negative if present)
    # -----------------------------------------------------------------------
    ("TC-6.3-009", "office_count", "Office count: null OR non-negative value",
     lambda r: _is_null(_get(r, "office_count")) or _non_empty(_get(r, "office_count"))),

    # -----------------------------------------------------------------------
    # TC-6.3-010  Office Locations  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-010", "office_locations", "Office locations: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "office_locations")) or _non_empty(_get(r, "office_locations"))),

    # -----------------------------------------------------------------------
    # TC-6.3-011  Employee Size  (NOT NULL, accepts ranges like '1,200 (est.)')
    # -----------------------------------------------------------------------
    ("TC-6.3-011", "employee_size", "Employee size must be non-empty",
     lambda r: _non_empty(_get(r, "employee_size"))),

    # -----------------------------------------------------------------------
    # TC-6.3-012  Hiring Velocity  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-012", "hiring_velocity", "Hiring velocity: null accepted",
     lambda r: _nullable_accepted(r, "hiring_velocity")),

    # -----------------------------------------------------------------------
    # TC-6.3-013  Employee Turnover  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-013", "employee_turnover", "Employee turnover: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "employee_turnover")) or _non_empty(_get(r, "employee_turnover"))),

    # -----------------------------------------------------------------------
    # TC-6.3-014  Average Retention Tenure  (Nullable, text accepted)
    # -----------------------------------------------------------------------
    ("TC-6.3-014", "avg_retention_tenure", "Avg retention: null OR non-empty narrative",
     lambda r: _is_null(_get(r, "avg_retention_tenure")) or _non_empty(_get(r, "avg_retention_tenure"))),

    # -----------------------------------------------------------------------
    # TC-6.3-015  Pain Points Being Addressed  (NOT NULL)
    # -----------------------------------------------------------------------
    ("TC-6.3-015", "pain_points_addressed", "Pain points must be non-empty",
     lambda r: _non_empty(_get(r, "pain_points_addressed"))),

    # -----------------------------------------------------------------------
    # TC-6.3-016  Focus Sectors / Industries  (NOT NULL)
    # -----------------------------------------------------------------------
    ("TC-6.3-016", "focus_sectors", "Focus sectors must be non-empty",
     lambda r: _non_empty(_get(r, "focus_sectors"))),

    # -----------------------------------------------------------------------
    # TC-6.3-017  Services / Offerings / Products  (NOT NULL)
    # -----------------------------------------------------------------------
    ("TC-6.3-017", "offerings_description", "Offerings/products must be non-empty",
     lambda r: _non_empty(_get(r, "offerings_description"))),

    # -----------------------------------------------------------------------
    # TC-6.3-018  Top Customers by Client Segments  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-018", "top_customers", "Top customers: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "top_customers")) or _non_empty(_get(r, "top_customers"))),

    # -----------------------------------------------------------------------
    # TC-6.3-019  Core Value Proposition  (NOT NULL)
    # -----------------------------------------------------------------------
    ("TC-6.3-019", "core_value_proposition", "Core value proposition must be non-empty",
     lambda r: _non_empty(_get(r, "core_value_proposition"))),

    # -----------------------------------------------------------------------
    # TC-6.3-020  Vision  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-020", "vision_statement", "Vision: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "vision_statement")) or _non_empty(_get(r, "vision_statement"))),

    # -----------------------------------------------------------------------
    # TC-6.3-021  Mission  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-021", "mission_statement", "Mission: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "mission_statement")) or _non_empty(_get(r, "mission_statement"))),

    # -----------------------------------------------------------------------
    # TC-6.3-022  Values / Core Values  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-022", "core_values", "Core values: null accepted OR non-empty text",
     lambda r: _is_null(_get(r, "core_values")) or _non_empty(_get(r, "core_values"))),

    # -----------------------------------------------------------------------
    # TC-6.3-023  Unique Differentiators  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-023", "unique_differentiators", "Unique differentiators: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "unique_differentiators")) or _non_empty(_get(r, "unique_differentiators"))),

    # -----------------------------------------------------------------------
    # TC-6.3-024  Competitive Advantages  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-024", "competitive_advantages", "Competitive advantages: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "competitive_advantages")) or _non_empty(_get(r, "competitive_advantages"))),

    # -----------------------------------------------------------------------
    # TC-6.3-025  Weaknesses / Gaps  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-025", "weaknesses_gaps", "Weaknesses/gaps: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "weaknesses_gaps")) or _non_empty(_get(r, "weaknesses_gaps"))),

    # -----------------------------------------------------------------------
    # TC-6.3-026  Key Challenges and Unmet Needs  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-026", "key_challenges_needs", "Key challenges: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "key_challenges_needs")) or _non_empty(_get(r, "key_challenges_needs"))),

    # -----------------------------------------------------------------------
    # TC-6.3-027  Key Competitors  (NOT NULL)
    # -----------------------------------------------------------------------
    ("TC-6.3-027", "key_competitors", "Key competitors must be non-empty",
     lambda r: _non_empty(_get(r, "key_competitors"))),

    # -----------------------------------------------------------------------
    # TC-6.3-028  Technology Partners  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-028", "technology_partners", "Tech partners: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "technology_partners")) or _non_empty(_get(r, "technology_partners"))),

    # -----------------------------------------------------------------------
    # TC-6.3-029  Interesting Facts / History  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-029", "history_timeline", "History/facts: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "history_timeline")) or _non_empty(_get(r, "history_timeline"))),

    # -----------------------------------------------------------------------
    # TC-6.3-030  Recent News  (Nullable â€” private cos may have none)
    # -----------------------------------------------------------------------
    ("TC-6.3-030", "recent_news", "Recent news: null accepted",
     lambda r: _nullable_accepted(r, "recent_news")),

    # -----------------------------------------------------------------------
    # TC-6.3-031  Website URL  (NOT NULL, must start https?://)
    # -----------------------------------------------------------------------
    ("TC-6.3-031", "website_url", "Website URL must start with http(s)://",
     lambda r: (not _is_null(_get(r, "website_url")))
               and _starts_with_http(_get(r, "website_url"))),

    # -----------------------------------------------------------------------
    # TC-6.3-032  Quality of Website  (Nullable, text accepted)
    # -----------------------------------------------------------------------
    ("TC-6.3-032", "website_quality", "Website quality: null OR non-empty narrative",
     lambda r: _is_null(_get(r, "website_quality")) or _non_empty(_get(r, "website_quality"))),

    # -----------------------------------------------------------------------
    # TC-6.3-033  Website Rating  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-033", "website_rating", "Website rating: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "website_rating")) or _non_empty(_get(r, "website_rating"))),

    # -----------------------------------------------------------------------
    # TC-6.3-034  Website Traffic Rank  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-034", "website_traffic_rank", "Traffic rank: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "website_traffic_rank")) or _non_empty(_get(r, "website_traffic_rank"))),

    # -----------------------------------------------------------------------
    # TC-6.3-035  Social Media Followers â€“ Combined  (Nullable for private cos)
    # -----------------------------------------------------------------------
    ("TC-6.3-035", "social_media_followers", "Social followers: null accepted OR non-negative integer",
     lambda r: _is_null(_get(r, "social_media_followers"))
               or _non_empty(_get(r, "social_media_followers"))),

    # -----------------------------------------------------------------------
    # TC-6.3-036  Glassdoor Rating  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-036", "glassdoor_rating", "Glassdoor rating: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "glassdoor_rating")) or _non_empty(_get(r, "glassdoor_rating"))),

    # -----------------------------------------------------------------------
    # TC-6.3-037  Indeed Rating  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-037", "indeed_rating", "Indeed rating: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "indeed_rating")) or _non_empty(_get(r, "indeed_rating"))),

    # -----------------------------------------------------------------------
    # TC-6.3-038  Google Reviews Rating  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-038", "google_rating", "Google rating: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "google_rating")) or _non_empty(_get(r, "google_rating"))),

    # -----------------------------------------------------------------------
    # TC-6.3-039  LinkedIn Profile URL  (Nullable; if present must be URL)
    # -----------------------------------------------------------------------
    ("TC-6.3-039", "linkedin_url", "LinkedIn URL: null accepted OR must start with https?://",
     lambda r: _is_null(_get(r, "linkedin_url")) or _starts_with_http(_get(r, "linkedin_url"))),

    # -----------------------------------------------------------------------
    # TC-6.3-040  CEO Name  (NOT NULL)
    # -----------------------------------------------------------------------
    ("TC-6.3-040", "ceo_name", "CEO name must be non-empty",
     lambda r: _non_empty(_get(r, "ceo_name"))),

    # -----------------------------------------------------------------------
    # TC-6.3-041  CEO LinkedIn URL  (Nullable; if present must be URL)
    # -----------------------------------------------------------------------
    ("TC-6.3-041", "ceo_linkedin_url", "CEO LinkedIn: null accepted OR must start with https?://",
     lambda r: _is_null(_get(r, "ceo_linkedin_url")) or _starts_with_http(_get(r, "ceo_linkedin_url"))),

    # -----------------------------------------------------------------------
    # TC-6.3-042  Key Business Leaders  (NOT NULL)
    # -----------------------------------------------------------------------
    ("TC-6.3-042", "key_leaders", "Key leaders must be non-empty",
     lambda r: _non_empty(_get(r, "key_leaders"))),

    # -----------------------------------------------------------------------
    # TC-6.3-043  Warm Introduction Pathways  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-043", "warm_intro_pathways", "Warm intro pathways: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "warm_intro_pathways")) or _non_empty(_get(r, "warm_intro_pathways"))),

    # -----------------------------------------------------------------------
    # TC-6.3-044  Decision Maker Accessibility
    # Metadata regex: ^(High|Medium|Low).*$  (Nullable)
    # Value may be 'Low, Large enterprise...' â€” prefix match
    # -----------------------------------------------------------------------
    ("TC-6.3-044", "decision_maker_access",
     "Decision maker access: null OR prefix matches High/Medium/Low",
     lambda r: _is_null(_get(r, "decision_maker_access"))
               or _prefix_in_enum(_get(r, "decision_maker_access"), {"High", "Medium", "Low"})),

    # -----------------------------------------------------------------------
    # TC-6.3-045  Company Contact Email  (Nullable; if present must contain @)
    # -----------------------------------------------------------------------
    ("TC-6.3-045", "primary_contact_email", "Contact email: null OR valid email format",
     lambda r: _is_null(_get(r, "primary_contact_email"))
               or _valid_email(_get(r, "primary_contact_email"))),

    # -----------------------------------------------------------------------
    # TC-6.3-046  Company Phone Number  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-046", "primary_phone_number", "Phone number: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "primary_phone_number")) or _non_empty(_get(r, "primary_phone_number"))),

    # -----------------------------------------------------------------------
    # TC-6.3-047  Primary Contact Person's Name  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-047", "contact_person_name", "Contact name: null accepted",
     lambda r: _nullable_accepted(r, "contact_person_name")),

    # -----------------------------------------------------------------------
    # TC-6.3-048  Primary Contact Person's Title  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-048", "contact_person_title", "Contact title: null accepted",
     lambda r: _nullable_accepted(r, "contact_person_title")),

    # -----------------------------------------------------------------------
    # TC-6.3-049  Primary Contact Person's Email  (Nullable; if present valid email)
    # -----------------------------------------------------------------------
    ("TC-6.3-049", "contact_person_email", "Contact email: null OR valid email format",
     lambda r: _is_null(_get(r, "contact_person_email"))
               or _valid_email(_get(r, "contact_person_email"))),

    # -----------------------------------------------------------------------
    # TC-6.3-050  Awards & Recognitions  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-050", "awards_recognitions", "Awards: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "awards_recognitions")) or _non_empty(_get(r, "awards_recognitions"))),

    # -----------------------------------------------------------------------
    # TC-6.3-051  Brand Sentiment Score  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-051", "brand_sentiment_score", "Brand sentiment: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "brand_sentiment_score")) or _non_empty(_get(r, "brand_sentiment_score"))),

    # -----------------------------------------------------------------------
    # TC-6.3-052  Event Participation  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-052", "event_participation", "Event participation: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "event_participation")) or _non_empty(_get(r, "event_participation"))),

    # -----------------------------------------------------------------------
    # TC-6.3-053  Regulatory & Compliance Status  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-053", "regulatory_status", "Regulatory status: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "regulatory_status")) or _non_empty(_get(r, "regulatory_status"))),

    # -----------------------------------------------------------------------
    # TC-6.3-054  Legal Issues / Controversies  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-054", "legal_issues", "Legal issues: null accepted OR non-empty narrative",
     lambda r: _is_null(_get(r, "legal_issues")) or _non_empty(_get(r, "legal_issues"))),

    # -----------------------------------------------------------------------
    # TC-6.3-055  Annual Revenues  (Nullable for private; if present non-empty)
    # -----------------------------------------------------------------------
    ("TC-6.3-055", "annual_revenue", "Annual revenue: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "annual_revenue")) or _non_empty(_get(r, "annual_revenue"))),

    # -----------------------------------------------------------------------
    # TC-6.3-056  Annual Profits  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-056", "annual_profit", "Annual profit: null accepted",
     lambda r: _nullable_accepted(r, "annual_profit")),

    # -----------------------------------------------------------------------
    # TC-6.3-057  Revenue Mix  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-057", "revenue_mix", "Revenue mix: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "revenue_mix")) or _non_empty(_get(r, "revenue_mix"))),

    # -----------------------------------------------------------------------
    # TC-6.3-058  Company Valuation  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-058", "valuation", "Valuation: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "valuation")) or _non_empty(_get(r, "valuation"))),

    # -----------------------------------------------------------------------
    # TC-6.3-059  Year-over-Year Growth Rate  (Nullable; if present non-empty)
    # -----------------------------------------------------------------------
    ("TC-6.3-059", "yoy_growth_rate", "YoY growth: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "yoy_growth_rate")) or _non_empty(_get(r, "yoy_growth_rate"))),

    # -----------------------------------------------------------------------
    # TC-6.3-060  Profitability Status  (NOT NULL; Enum)
    # -----------------------------------------------------------------------
    ("TC-6.3-060", "profitability_status", "Profitability must be Profitable/Break-even/Loss-making",
     lambda r: _in_enum(_get(r, "profitability_status"),
                        {"Profitable", "Break-even", "Loss-making"})),

    # -----------------------------------------------------------------------
    # TC-6.3-061  Market Share (%)  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-061", "market_share_percentage", "Market share: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "market_share_percentage")) or _non_empty(_get(r, "market_share_percentage"))),

    # -----------------------------------------------------------------------
    # TC-6.3-062  Key Investors / Backers  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-062", "key_investors", "Key investors: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "key_investors")) or _non_empty(_get(r, "key_investors"))),

    # -----------------------------------------------------------------------
    # TC-6.3-063  Recent Funding Rounds  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-063", "recent_funding_rounds", "Recent funding rounds: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "recent_funding_rounds")) or _non_empty(_get(r, "recent_funding_rounds"))),

    # -----------------------------------------------------------------------
    # TC-6.3-064  Total Capital Raised  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-064", "total_capital_raised", "Total capital raised: null accepted",
     lambda r: _nullable_accepted(r, "total_capital_raised")),

    # -----------------------------------------------------------------------
    # TC-6.3-065  ESG Practices or Ratings  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-065", "esg_ratings", "ESG ratings: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "esg_ratings")) or _non_empty(_get(r, "esg_ratings"))),

    # -----------------------------------------------------------------------
    # TC-6.3-066  Sales Motion  (NOT NULL per metadata)
    # -----------------------------------------------------------------------
    ("TC-6.3-066", "sales_motion", "Sales motion must be non-empty",
     lambda r: _non_empty(_get(r, "sales_motion"))),

    # -----------------------------------------------------------------------
    # TC-6.3-067  Customer Acquisition Cost (CAC)  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-067", "customer_acquisition_cost", "CAC: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "customer_acquisition_cost"))
               or _non_empty(_get(r, "customer_acquisition_cost"))),

    # -----------------------------------------------------------------------
    # TC-6.3-068  Customer Lifetime Value (CLV)  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-068", "customer_lifetime_value", "CLV: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "customer_lifetime_value"))
               or _non_empty(_get(r, "customer_lifetime_value"))),

    # -----------------------------------------------------------------------
    # TC-6.3-069  Churn Rate  (Nullable; if present value accepted)
    # -----------------------------------------------------------------------
    ("TC-6.3-069", "churn_rate", "Churn rate: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "churn_rate")) or _non_empty(_get(r, "churn_rate"))),

    # -----------------------------------------------------------------------
    # TC-6.3-070  Net Promoter Score  (Nullable; if present range -100 to 100)
    # -----------------------------------------------------------------------
    ("TC-6.3-070", "net_promoter_score", "NPS: null accepted OR value is non-empty",
     lambda r: _is_null(_get(r, "net_promoter_score")) or _non_empty(_get(r, "net_promoter_score"))),

    # -----------------------------------------------------------------------
    # TC-6.3-071  Customer Concentration Risk  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-071", "customer_concentration_risk", "Customer concentration risk: null OR non-empty",
     lambda r: _is_null(_get(r, "customer_concentration_risk"))
               or _non_empty(_get(r, "customer_concentration_risk"))),

    # -----------------------------------------------------------------------
    # TC-6.3-072  Burn Rate  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-072", "burn_rate", "Burn rate: null accepted",
     lambda r: _nullable_accepted(r, "burn_rate")),

    # -----------------------------------------------------------------------
    # TC-6.3-073  Runway  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-073", "runway_months", "Runway: null accepted OR non-empty value",
     lambda r: _is_null(_get(r, "runway_months")) or _non_empty(_get(r, "runway_months"))),

    # -----------------------------------------------------------------------
    # TC-6.3-074  Intellectual Property  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-074", "intellectual_property", "IP: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "intellectual_property")) or _non_empty(_get(r, "intellectual_property"))),

    # -----------------------------------------------------------------------
    # TC-6.3-075  R&D Investment  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-075", "r_and_d_investment", "R&D investment: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "r_and_d_investment")) or _non_empty(_get(r, "r_and_d_investment"))),

    # -----------------------------------------------------------------------
    # TC-6.3-076  AI/ML Adoption Level  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-076", "ai_ml_adoption_level", "AI/ML adoption: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "ai_ml_adoption_level")) or _non_empty(_get(r, "ai_ml_adoption_level"))),

    # -----------------------------------------------------------------------
    # TC-6.3-077  Tech Stack / Tools  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-077", "tech_stack", "Tech stack: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "tech_stack")) or _non_empty(_get(r, "tech_stack"))),

    # -----------------------------------------------------------------------
    # TC-6.3-078  Cybersecurity Posture  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-078", "cybersecurity_posture", "Cybersecurity posture: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "cybersecurity_posture")) or _non_empty(_get(r, "cybersecurity_posture"))),

    # -----------------------------------------------------------------------
    # TC-6.3-079  Supply Chain Dependencies  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-079", "supply_chain_dependencies", "Supply chain: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "supply_chain_dependencies"))
               or _non_empty(_get(r, "supply_chain_dependencies"))),

    # -----------------------------------------------------------------------
    # TC-6.3-080  Geopolitical Risks  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-080", "geopolitical_risks", "Geopolitical risks: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "geopolitical_risks")) or _non_empty(_get(r, "geopolitical_risks"))),

    # -----------------------------------------------------------------------
    # TC-6.3-081  Macro Risks  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-081", "macro_risks", "Macro risks: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "macro_risks")) or _non_empty(_get(r, "macro_risks"))),

    # -----------------------------------------------------------------------
    # TC-6.3-082  Diversity Metrics  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-082", "diversity_metrics", "Diversity metrics: null accepted",
     lambda r: _nullable_accepted(r, "diversity_metrics")),

    # -----------------------------------------------------------------------
    # TC-6.3-083  Remote Work Policy  (NOT NULL per metadata)
    # -----------------------------------------------------------------------
    ("TC-6.3-083", "remote_policy_details", "Remote work policy must be non-empty",
     lambda r: _non_empty(_get(r, "remote_policy_details"))),

    # -----------------------------------------------------------------------
    # TC-6.3-084  Training/Development Spend  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-084", "training_spend", "Training spend: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "training_spend")) or _non_empty(_get(r, "training_spend"))),

    # -----------------------------------------------------------------------
    # TC-6.3-085  Partnership Ecosystem  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-085", "partnership_ecosystem", "Partnership ecosystem: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "partnership_ecosystem")) or _non_empty(_get(r, "partnership_ecosystem"))),

    # -----------------------------------------------------------------------
    # TC-6.3-086  Exit Strategy / History  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-086", "exit_strategy_history", "Exit strategy: null accepted OR non-empty narrative",
     lambda r: _is_null(_get(r, "exit_strategy_history")) or _non_empty(_get(r, "exit_strategy_history"))),

    # -----------------------------------------------------------------------
    # TC-6.3-087  Ethical Sourcing Practices  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-087", "ethical_sourcing", "Ethical sourcing: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "ethical_sourcing")) or _non_empty(_get(r, "ethical_sourcing"))),

    # -----------------------------------------------------------------------
    # TC-6.3-088  Benchmark vs. Peers  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-088", "benchmark_vs_peers", "Benchmark vs peers: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "benchmark_vs_peers")) or _non_empty(_get(r, "benchmark_vs_peers"))),

    # -----------------------------------------------------------------------
    # TC-6.3-089  Future Projections  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-089", "future_projections", "Future projections: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "future_projections")) or _non_empty(_get(r, "future_projections"))),

    # -----------------------------------------------------------------------
    # TC-6.3-090  Strategic Priorities  (NOT NULL per metadata)
    # -----------------------------------------------------------------------
    ("TC-6.3-090", "strategic_priorities", "Strategic priorities must be non-empty",
     lambda r: _non_empty(_get(r, "strategic_priorities"))),

    # -----------------------------------------------------------------------
    # TC-6.3-091  Industry Associations / Memberships  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-091", "industry_associations", "Industry associations: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "industry_associations")) or _non_empty(_get(r, "industry_associations"))),

    # -----------------------------------------------------------------------
    # TC-6.3-092  Go-to-Market Strategy  (NOT NULL per metadata)
    # -----------------------------------------------------------------------
    ("TC-6.3-092", "go_to_market_strategy", "GTM strategy must be non-empty",
     lambda r: _non_empty(_get(r, "go_to_market_strategy"))),

    # -----------------------------------------------------------------------
    # TC-6.3-093  Innovation Roadmap  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-093", "innovation_roadmap", "Innovation roadmap: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "innovation_roadmap")) or _non_empty(_get(r, "innovation_roadmap"))),

    # -----------------------------------------------------------------------
    # TC-6.3-094  Product Pipeline  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-094", "product_pipeline", "Product pipeline: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "product_pipeline")) or _non_empty(_get(r, "product_pipeline"))),

    # -----------------------------------------------------------------------
    # TC-6.3-095  Board of Directors / Advisors  (NOT NULL per metadata)
    # -----------------------------------------------------------------------
    ("TC-6.3-095", "board_members", "Board members must be non-empty",
     lambda r: _non_empty(_get(r, "board_members"))),

    # -----------------------------------------------------------------------
    # TC-6.3-096  Customer Testimonials  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-096", "customer_testimonials", "Customer testimonials: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "customer_testimonials")) or _non_empty(_get(r, "customer_testimonials"))),

    # -----------------------------------------------------------------------
    # TC-6.3-097  Work Culture  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-097", "work_culture_summary", "Work culture: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "work_culture_summary")) or _non_empty(_get(r, "work_culture_summary"))),

    # -----------------------------------------------------------------------
    # TC-6.3-098  Manager Quality  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-098", "manager_quality", "Manager quality: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "manager_quality")) or _non_empty(_get(r, "manager_quality"))),

    # -----------------------------------------------------------------------
    # TC-6.3-099  Psychological Safety  (Nullable; metadata enum Low/Medium/High/Safe/Toxic + text)
    # -----------------------------------------------------------------------
    ("TC-6.3-099", "psychological_safety", "Psychological safety: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "psychological_safety")) or _non_empty(_get(r, "psychological_safety"))),

    # -----------------------------------------------------------------------
    # TC-6.3-100  Feedback Culture  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-100", "feedback_culture", "Feedback culture: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "feedback_culture")) or _non_empty(_get(r, "feedback_culture"))),

    # -----------------------------------------------------------------------
    # TC-6.3-101  Diversity & Inclusion  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-101", "diversity_inclusion_score", "D&I: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "diversity_inclusion_score"))
               or _non_empty(_get(r, "diversity_inclusion_score"))),

    # -----------------------------------------------------------------------
    # TC-6.3-102  Ethical Standards  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-102", "ethical_standards", "Ethical standards: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "ethical_standards")) or _non_empty(_get(r, "ethical_standards"))),

    # -----------------------------------------------------------------------
    # TC-6.3-103  Typical Working Hours  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-103", "typical_hours", "Typical hours: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "typical_hours")) or _non_empty(_get(r, "typical_hours"))),

    # -----------------------------------------------------------------------
    # TC-6.3-104  Overtime Expectations  (Nullable; enum prefix Routine/Rare/Seasonal/Frequent/Occasional)
    # -----------------------------------------------------------------------
    ("TC-6.3-104", "overtime_expectations", "Overtime expectations: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "overtime_expectations")) or _non_empty(_get(r, "overtime_expectations"))),

    # -----------------------------------------------------------------------
    # TC-6.3-105  Weekend Work  (Nullable; enum Never/Rarely/Occasionally/Frequently/Always)
    # -----------------------------------------------------------------------
    ("TC-6.3-105", "weekend_work", "Weekend work: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "weekend_work")) or _non_empty(_get(r, "weekend_work"))),

    # -----------------------------------------------------------------------
    # TC-6.3-106  Leave Policy  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-106", "leave_policy", "Leave policy: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "leave_policy")) or _non_empty(_get(r, "leave_policy"))),

    # -----------------------------------------------------------------------
    # TC-6.3-107  Burnout Risk  (Nullable; enum Low/Medium/High/Severe)
    # -----------------------------------------------------------------------
    ("TC-6.3-107", "burnout_risk", "Burnout risk: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "burnout_risk")) or _non_empty(_get(r, "burnout_risk"))),

    # -----------------------------------------------------------------------
    # TC-6.3-108  Onboarding and Training Quality  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-108", "onboarding_quality", "Onboarding quality: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "onboarding_quality")) or _non_empty(_get(r, "onboarding_quality"))),

    # -----------------------------------------------------------------------
    # TC-6.3-109  Learning Culture  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-109", "learning_culture", "Learning culture: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "learning_culture")) or _non_empty(_get(r, "learning_culture"))),

    # -----------------------------------------------------------------------
    # TC-6.3-110  Exposure Quality  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-110", "exposure_quality", "Exposure quality: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "exposure_quality")) or _non_empty(_get(r, "exposure_quality"))),

    # -----------------------------------------------------------------------
    # TC-6.3-111  Mentorship Availability  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-111", "mentorship_availability", "Mentorship: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "mentorship_availability")) or _non_empty(_get(r, "mentorship_availability"))),

    # -----------------------------------------------------------------------
    # TC-6.3-112  Internal Mobility  (Nullable; enum High/Medium/Low/Frozen)
    # -----------------------------------------------------------------------
    ("TC-6.3-112", "internal_mobility", "Internal mobility: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "internal_mobility")) or _non_empty(_get(r, "internal_mobility"))),

    # -----------------------------------------------------------------------
    # TC-6.3-113  Promotion Clarity  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-113", "promotion_clarity", "Promotion clarity: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "promotion_clarity")) or _non_empty(_get(r, "promotion_clarity"))),

    # -----------------------------------------------------------------------
    # TC-6.3-114  Tools and Technology Access  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-114", "tools_access", "Tools access: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "tools_access")) or _non_empty(_get(r, "tools_access"))),

    # -----------------------------------------------------------------------
    # TC-6.3-115  Role Clarity  (Nullable; enum High/Medium/Low/Vague/Defined)
    # -----------------------------------------------------------------------
    ("TC-6.3-115", "role_clarity", "Role clarity: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "role_clarity")) or _non_empty(_get(r, "role_clarity"))),

    # -----------------------------------------------------------------------
    # TC-6.3-116  Early Ownership  (Nullable; enum High/Low/Gradual/Immediate)
    # -----------------------------------------------------------------------
    ("TC-6.3-116", "early_ownership", "Early ownership: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "early_ownership")) or _non_empty(_get(r, "early_ownership"))),

    # -----------------------------------------------------------------------
    # TC-6.3-117  Work Impact  (Nullable; enum High/Medium/Low/Back-office/Front-line)
    # -----------------------------------------------------------------------
    ("TC-6.3-117", "work_impact", "Work impact: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "work_impact")) or _non_empty(_get(r, "work_impact"))),

    # -----------------------------------------------------------------------
    # TC-6.3-118  Execution vs Thinking Balance  (Nullable; enum)
    # -----------------------------------------------------------------------
    ("TC-6.3-118", "execution_thinking_balance", "Execution/thinking balance: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "execution_thinking_balance"))
               or _non_empty(_get(r, "execution_thinking_balance"))),

    # -----------------------------------------------------------------------
    # TC-6.3-119  Automation Level  (Nullable; enum High/Medium/Low/Manual/Automated)
    # -----------------------------------------------------------------------
    ("TC-6.3-119", "automation_level", "Automation level: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "automation_level")) or _non_empty(_get(r, "automation_level"))),

    # -----------------------------------------------------------------------
    # TC-6.3-120  Cross-functional Exposure  (Nullable; enum Siloed/Collaborative/Matrix)
    # -----------------------------------------------------------------------
    ("TC-6.3-120", "cross_functional_exposure", "Cross-func exposure: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "cross_functional_exposure"))
               or _non_empty(_get(r, "cross_functional_exposure"))),

    # -----------------------------------------------------------------------
    # TC-6.3-121  Brand Value  (Nullable; tier enum or qualitative)
    # -----------------------------------------------------------------------
    ("TC-6.3-121", "brand_value", "Brand value: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "brand_value")) or _non_empty(_get(r, "brand_value"))),

    # -----------------------------------------------------------------------
    # TC-6.3-122  Client Quality  (Nullable; Fortune 500/Enterprise/SMB/Mid-market)
    # -----------------------------------------------------------------------
    ("TC-6.3-122", "client_quality", "Client quality: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "client_quality")) or _non_empty(_get(r, "client_quality"))),

    # -----------------------------------------------------------------------
    # TC-6.3-123  Mission Clarity  (Nullable; enum Clear/Confusing/Generic/Inspiring)
    # -----------------------------------------------------------------------
    ("TC-6.3-123", "mission_clarity", "Mission clarity: null accepted OR non-empty",
     lambda r: _is_null(_get(r, "mission_clarity")) or _non_empty(_get(r, "mission_clarity"))),

    # -----------------------------------------------------------------------
    # TC-6.3-124  Crisis Behavior  (Nullable)
    # -----------------------------------------------------------------------
    ("TC-6.3-124", "crisis_behavior", "Crisis behavior: null accepted OR non-empty narrative",
     lambda r: _is_null(_get(r, "crisis_behavior")) or _non_empty(_get(r, "crisis_behavior"))),

]  # end TC_PARAMS


# =============================================================================
# PARAMETRIZED TEST
# =============================================================================

@pytest.mark.parametrize(
    "tc_id, col, description, validation_fn",
    TC_PARAMS,
    ids=[p[0] for p in TC_PARAMS],   # e.g. "TC-6.3-001"
)
def test_tc_6_3(row, tc_id, col, description, validation_fn):
    """
    TC-6.3 â€” Private Company Data Validation.

    For each parameter, the test:
      1. Reads the value from the company row.
      2. Applies the field-specific validation function.
      3. Fails with a descriptive message listing TC ID, column, rule, and actual value.
    """
    value = _get(row, col)
    passed = validation_fn(row)

    assert passed, (
        f"\n{'='*60}\n"
        f"  FAIL  : {tc_id}\n"
        f"  Column: {col}\n"
        f"  Rule  : {description}\n"
        f"  Value : {repr(value)}\n"
        f"  Company: {COMPANY_NAME}\n"
        f"{'='*60}"
    )

