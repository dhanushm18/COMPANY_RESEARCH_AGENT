from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .schema import ParameterSpec

# staging_id is SERIAL in DB, so it is intentionally omitted from export columns.
STAGING_EXPORT_COLUMNS = [
    "company_id",
    "name",
    "short_name",
    "logo_url",
    "category",
    "incorporation_year",
    "overview_text",
    "nature_of_company",
    "headquarters_address",
    "operating_countries",
    "office_count",
    "office_locations",
    "employee_size",
    "hiring_velocity",
    "employee_turnover",
    "avg_retention_tenure",
    "pain_points_addressed",
    "focus_sectors",
    "offerings_description",
    "top_customers",
    "core_value_proposition",
    "vision_statement",
    "mission_statement",
    "core_values",
    "unique_differentiators",
    "competitive_advantages",
    "weaknesses_gaps",
    "key_challenges_needs",
    "key_competitors",
    "technology_partners",
    "history_timeline",
    "recent_news",
    "website_url",
    "website_quality",
    "website_rating",
    "website_traffic_rank",
    "social_media_followers",
    "glassdoor_rating",
    "indeed_rating",
    "google_rating",
    "linkedin_url",
    "twitter_handle",
    "facebook_url",
    "instagram_url",
    "ceo_name",
    "ceo_linkedin_url",
    "key_leaders",
    "warm_intro_pathways",
    "decision_maker_access",
    "primary_contact_email",
    "primary_phone_number",
    "contact_person_name",
    "contact_person_title",
    "contact_person_email",
    "contact_person_phone",
    "awards_recognitions",
    "brand_sentiment_score",
    "event_participation",
    "regulatory_status",
    "legal_issues",
    "annual_revenue",
    "annual_profit",
    "revenue_mix",
    "valuation",
    "yoy_growth_rate",
    "profitability_status",
    "market_share_percentage",
    "key_investors",
    "recent_funding_rounds",
    "total_capital_raised",
    "esg_ratings",
    "sales_motion",
    "customer_acquisition_cost",
    "customer_lifetime_value",
    "cac_ltv_ratio",
    "churn_rate",
    "net_promoter_score",
    "customer_concentration_risk",
    "burn_rate",
    "runway_months",
    "burn_multiplier",
    "intellectual_property",
    "r_and_d_investment",
    "ai_ml_adoption_level",
    "tech_stack",
    "cybersecurity_posture",
    "supply_chain_dependencies",
    "geopolitical_risks",
    "macro_risks",
    "diversity_metrics",
    "remote_policy_details",
    "training_spend",
    "partnership_ecosystem",
    "exit_strategy_history",
    "carbon_footprint",
    "ethical_sourcing",
    "benchmark_vs_peers",
    "future_projections",
    "strategic_priorities",
    "industry_associations",
    "case_studies",
    "go_to_market_strategy",
    "innovation_roadmap",
    "product_pipeline",
    "board_members",
    "marketing_video_url",
    "customer_testimonials",
    "tech_adoption_rating",
    "tam",
    "sam",
    "som",
    "work_culture_summary",
    "manager_quality",
    "psychological_safety",
    "feedback_culture",
    "diversity_inclusion_score",
    "ethical_standards",
    "typical_hours",
    "overtime_expectations",
    "weekend_work",
    "flexibility_level",
    "leave_policy",
    "burnout_risk",
    "location_centrality",
    "public_transport_access",
    "cab_policy",
    "airport_commute_time",
    "office_zone_type",
    "area_safety",
    "safety_policies",
    "infrastructure_safety",
    "emergency_preparedness",
    "health_support",
    "onboarding_quality",
    "learning_culture",
    "exposure_quality",
    "mentorship_availability",
    "internal_mobility",
    "promotion_clarity",
    "tools_access",
    "role_clarity",
    "early_ownership",
    "work_impact",
    "execution_thinking_balance",
    "automation_level",
    "cross_functional_exposure",
    "company_maturity",
    "brand_value",
    "client_quality",
    "layoff_history",
    "fixed_vs_variable_pay",
    "bonus_predictability",
    "esops_incentives",
    "family_health_insurance",
    "relocation_support",
    "lifestyle_benefits",
    "exit_opportunities",
    "skill_relevance",
    "external_recognition",
    "network_strength",
    "global_exposure",
    "mission_clarity",
    "sustainability_csr",
    "crisis_behavior",
]


def build_ready_for_db_records(
    consolidated_payload: dict[str, Any],
    specs: list[ParameterSpec],
    company_id_start: int = 1,
) -> list[dict[str, Any]]:
    # IDs 1..N in schema correspond to staging columns after company_id.
    data_columns = [c for c in STAGING_EXPORT_COLUMNS if c != "company_id"]
    sorted_specs = sorted(specs, key=lambda s: s.sr_no)
    id_to_db_col: dict[int, str] = {}
    for i, spec in enumerate(sorted_specs):
        if i >= len(data_columns):
            break
        id_to_db_col[spec.sr_no] = data_columns[i]

    records: list[dict[str, Any]] = []

    companies = consolidated_payload.get("consolidated_rows", [])
    for idx, company in enumerate(companies, start=company_id_start):
        company_name = str(company.get("company_name", "")).strip()
        row = {c: "" for c in STAGING_EXPORT_COLUMNS}
        row["company_id"] = idx

        for r in company.get("rows", []):
            rid = str(r.get("ID", "")).strip()
            if not rid.isdigit():
                continue
            col = id_to_db_col.get(int(rid))
            if col in row:
                row[col] = str(r.get("Research Output / Data", "") or "").strip()

        if not row.get("name"):
            row["name"] = company_name
        records.append(row)

    return records


def write_ready_for_db_csv(path: str | Path, records: list[dict[str, Any]]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=STAGING_EXPORT_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow({c: record.get(c, "") for c in STAGING_EXPORT_COLUMNS})
    return out


def write_ready_for_db_json(path: str | Path, records: list[dict[str, Any]]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
