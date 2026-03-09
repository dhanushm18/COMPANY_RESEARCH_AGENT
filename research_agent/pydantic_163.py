from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Company163Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    company_name: str | None = Field(default=None, alias="Company Name", description="ID 1")
    short_name: str | None = Field(default=None, alias="Short Name", description="ID 2")
    logo: str | None = Field(default=None, alias="Logo", description="ID 3")
    category: str | None = Field(default=None, alias="Category", description="ID 4")
    year_of_incorporation: str | None = Field(default=None, alias="Year of Incorporation", description="ID 5")
    overview_of_the_company: str | None = Field(default=None, alias="Overview of the Company", description="ID 6")
    nature_of_company: str | None = Field(default=None, alias="Nature of Company", description="ID 7")
    company_headquarters: str | None = Field(default=None, alias="Company Headquarters", description="ID 8")
    countries_operating_in: str | None = Field(default=None, alias="Countries Operating In", description="ID 9")
    number_of_offices_beyond_hq: str | None = Field(default=None, alias="Number of Offices (beyond HQ)", description="ID 10")
    office_locations: str | None = Field(default=None, alias="Office Locations", description="ID 11")
    employee_size: str | None = Field(default=None, alias="Employee Size", description="ID 12")
    hiring_velocity: str | None = Field(default=None, alias="Hiring Velocity", description="ID 13")
    employee_turnover: str | None = Field(default=None, alias="Employee Turnover", description="ID 14")
    average_retention_tenure: str | None = Field(default=None, alias="Average Retention Tenure", description="ID 15")
    pain_points_being_addressed: str | None = Field(default=None, alias="Pain Points Being Addressed", description="ID 16")
    focus_sectors_industries: str | None = Field(default=None, alias="Focus Sectors / Industries", description="ID 17")
    services_offerings_products: str | None = Field(default=None, alias="Services / Offerings / Products", description="ID 18")
    top_customers_by_client_segments: str | None = Field(default=None, alias="Top Customers by Client Segments", description="ID 19")
    core_value_proposition: str | None = Field(default=None, alias="Core Value Proposition", description="ID 20")
    vision: str | None = Field(default=None, alias="Vision", description="ID 21")
    mission: str | None = Field(default=None, alias="Mission", description="ID 22")
    values: str | None = Field(default=None, alias="Values", description="ID 23")
    unique_differentiators: str | None = Field(default=None, alias="Unique Differentiators", description="ID 24")
    competitive_advantages: str | None = Field(default=None, alias="Competitive Advantages", description="ID 25")
    weaknesses_gaps_in_offering: str | None = Field(default=None, alias="Weaknesses / Gaps in Offering", description="ID 26")
    key_challenges_and_unmet_needs: str | None = Field(default=None, alias="Key Challenges and Unmet Needs", description="ID 27")
    key_competitors: str | None = Field(default=None, alias="Key Competitors", description="ID 28")
    technology_partners: str | None = Field(default=None, alias="Technology Partners", description="ID 29")
    interesting_facts: str | None = Field(default=None, alias="Interesting Facts", description="ID 30")
    recent_news: str | None = Field(default=None, alias="Recent News", description="ID 31")
    website_url: str | None = Field(default=None, alias="Website URL", description="ID 32")
    quality_of_website: str | None = Field(default=None, alias="Quality of Website", description="ID 33")
    website_rating: str | None = Field(default=None, alias="Website Rating", description="ID 34")
    website_traffic_rank: str | None = Field(default=None, alias="Website Traffic Rank", description="ID 35")
    social_media_followers_combined: str | None = Field(default=None, alias="Social Media Followers – Combined", description="ID 36")
    glassdoor_rating: str | None = Field(default=None, alias="Glassdoor Rating", description="ID 37")
    indeed_rating: str | None = Field(default=None, alias="Indeed Rating", description="ID 38")
    google_reviews_rating: str | None = Field(default=None, alias="Google Reviews Rating", description="ID 39")
    linkedin_profile_url: str | None = Field(default=None, alias="LinkedIn Profile URL", description="ID 40")
    twitter_x_handle: str | None = Field(default=None, alias="Twitter (X) Handle", description="ID 41")
    facebook_page_url: str | None = Field(default=None, alias="Facebook Page URL", description="ID 42")
    instagram_page_url: str | None = Field(default=None, alias="Instagram Page URL", description="ID 43")
    ceo_name: str | None = Field(default=None, alias="CEO Name", description="ID 44")
    ceo_linkedin_url: str | None = Field(default=None, alias="CEO LinkedIn URL", description="ID 45")
    key_business_leaders: str | None = Field(default=None, alias="Key Business Leaders", description="ID 46")
    warm_introduction_pathways: str | None = Field(default=None, alias="Warm Introduction Pathways", description="ID 47")
    decision_maker_accessibility: str | None = Field(default=None, alias="Decision Maker Accessibility", description="ID 48")
    company_contact_email: str | None = Field(default=None, alias="Company Contact Email", description="ID 49")
    company_phone_number: str | None = Field(default=None, alias="Company Phone Number", description="ID 50")
    primary_contact_person_s_name: str | None = Field(default=None, alias="Primary Contact Person's Name", description="ID 51")
    primary_contact_person_s_title: str | None = Field(default=None, alias="Primary Contact Person's Title", description="ID 52")
    primary_contact_person_s_email: str | None = Field(default=None, alias="Primary Contact Person's Email", description="ID 53")
    primary_contact_person_s_phone_number: str | None = Field(default=None, alias="Primary Contact Person's Phone Number", description="ID 54")
    awards_recognitions: str | None = Field(default=None, alias="Awards & Recognitions", description="ID 55")
    brand_sentiment_score: str | None = Field(default=None, alias="Brand Sentiment Score", description="ID 56")
    event_participation: str | None = Field(default=None, alias="Event Participation", description="ID 57")
    regulatory_compliance_status: str | None = Field(default=None, alias="Regulatory & Compliance Status", description="ID 58")
    legal_issues_controversies: str | None = Field(default=None, alias="Legal Issues / Controversies", description="ID 59")
    annual_revenues: str | None = Field(default=None, alias="Annual Revenues", description="ID 60")
    annual_profits: str | None = Field(default=None, alias="Annual Profits", description="ID 61")
    revenue_mix: str | None = Field(default=None, alias="Revenue Mix", description="ID 62")
    company_valuation: str | None = Field(default=None, alias="Company Valuation", description="ID 63")
    year_over_year_growth_rate: str | None = Field(default=None, alias="Year-over-Year Growth Rate", description="ID 64")
    profitability_status: str | None = Field(default=None, alias="Profitability Status", description="ID 65")
    market_share: str | None = Field(default=None, alias="Market Share (%)", description="ID 66")
    key_investors_backers: str | None = Field(default=None, alias="Key Investors / Backers", description="ID 67")
    recent_funding_rounds: str | None = Field(default=None, alias="Recent Funding Rounds", description="ID 68")
    total_capital_raised: str | None = Field(default=None, alias="Total Capital Raised", description="ID 69")
    esg_practices_or_ratings: str | None = Field(default=None, alias="ESG Practices or Ratings", description="ID 70")
    sales_motion: str | None = Field(default=None, alias="Sales Motion", description="ID 71")
    customer_acquisition_cost_cac: str | None = Field(default=None, alias="Customer Acquisition Cost (CAC)", description="ID 72")
    customer_lifetime_value_clv: str | None = Field(default=None, alias="Customer Lifetime Value (CLV)", description="ID 73")
    cac_ltv_ratio: str | None = Field(default=None, alias="CAC:LTV Ratio", description="ID 74")
    churn_rate: str | None = Field(default=None, alias="Churn Rate", description="ID 75")
    net_promoter_score_nps: str | None = Field(default=None, alias="Net Promoter Score (NPS)", description="ID 76")
    customer_concentration_risk: str | None = Field(default=None, alias="Customer Concentration Risk", description="ID 77")
    burn_rate: str | None = Field(default=None, alias="Burn Rate", description="ID 78")
    runway: str | None = Field(default=None, alias="Runway", description="ID 79")
    burn_multiplier: str | None = Field(default=None, alias="Burn Multiplier", description="ID 80")
    intellectual_property: str | None = Field(default=None, alias="Intellectual Property", description="ID 81")
    r_d_investment: str | None = Field(default=None, alias="R&D Investment", description="ID 82")
    ai_ml_adoption_level: str | None = Field(default=None, alias="AI/ML Adoption Level", description="ID 83")
    tech_stack_tools_used: str | None = Field(default=None, alias="Tech Stack/Tools Used", description="ID 84")
    cybersecurity_posture: str | None = Field(default=None, alias="Cybersecurity Posture", description="ID 85")
    supply_chain_dependencies: str | None = Field(default=None, alias="Supply Chain Dependencies", description="ID 86")
    geopolitical_risks: str | None = Field(default=None, alias="Geopolitical Risks", description="ID 87")
    macro_risks: str | None = Field(default=None, alias="Macro Risks", description="ID 88")
    diversity_metrics: str | None = Field(default=None, alias="Diversity Metrics", description="ID 89")
    remote_work_policy: str | None = Field(default=None, alias="Remote Work Policy", description="ID 90")
    training_development_spend: str | None = Field(default=None, alias="Training/Development Spend", description="ID 91")
    partnership_ecosystem: str | None = Field(default=None, alias="Partnership Ecosystem", description="ID 92")
    exit_strategy_history: str | None = Field(default=None, alias="Exit Strategy/History", description="ID 93")
    carbon_footprint_environmental_impact: str | None = Field(default=None, alias="Carbon Footprint/Environmental Impact", description="ID 94")
    ethical_sourcing_practices: str | None = Field(default=None, alias="Ethical Sourcing Practices", description="ID 95")
    benchmark_vs_peers: str | None = Field(default=None, alias="Benchmark vs. Peers", description="ID 96")
    future_projections: str | None = Field(default=None, alias="Future Projections", description="ID 97")
    strategic_priorities: str | None = Field(default=None, alias="Strategic Priorities", description="ID 98")
    industry_associations_memberships: str | None = Field(default=None, alias="Industry Associations / Memberships", description="ID 99")
    case_studies_public_success_stories: str | None = Field(default=None, alias="Case Studies / Public Success Stories", description="ID 100")
    go_to_market_strategy: str | None = Field(default=None, alias="Go-to-Market Strategy", description="ID 101")
    innovation_roadmap: str | None = Field(default=None, alias="Innovation Roadmap", description="ID 102")
    product_pipeline: str | None = Field(default=None, alias="Product Pipeline", description="ID 103")
    board_of_directors_advisors: str | None = Field(default=None, alias="Board of Directors / Advisors", description="ID 104")
    company_introduction_marketing_videos: str | None = Field(default=None, alias="Company Introduction / Marketing videos", description="ID 105")
    customer_testimonial: str | None = Field(default=None, alias="Customer testimonial", description="ID 106")
    industry_benchmark_technology_adoption_rating: str | None = Field(default=None, alias="Industry Benchmark Technology Adoption Rating", description="ID 107")
    total_addressable_market_tam: str | None = Field(default=None, alias="Total Addressable Market (TAM)", description="ID 108")
    serviceable_addressable_market_sam: str | None = Field(default=None, alias="Serviceable Addressable Market (SAM)", description="ID 109")
    serviceable_obtainable_market_som: str | None = Field(default=None, alias="Serviceable Obtainable Market (SOM)", description="ID 110")
    work_culture: str | None = Field(default=None, alias="Work culture", description="ID 111")
    manager_quality: str | None = Field(default=None, alias="Manager quality", description="ID 112")
    psychological_safety: str | None = Field(default=None, alias="Psychological safety", description="ID 113")
    feedback_culture: str | None = Field(default=None, alias="Feedback culture", description="ID 114")
    diversity_inclusion: str | None = Field(default=None, alias="Diversity & inclusion", description="ID 115")
    ethical_standards: str | None = Field(default=None, alias="Ethical standards", description="ID 116")
    typical_working_hours: str | None = Field(default=None, alias="Typical working hours", description="ID 117")
    overtime_expectations: str | None = Field(default=None, alias="Overtime expectations", description="ID 118")
    weekend_work: str | None = Field(default=None, alias="Weekend work", description="ID 119")
    remote_hybrid_on_site_flexibility: str | None = Field(default=None, alias="Remote / hybrid / on-site flexibility", description="ID 120")
    leave_policy: str | None = Field(default=None, alias="Leave policy", description="ID 121")
    burnout_risk: str | None = Field(default=None, alias="Burnout risk", description="ID 122")
    central_vs_peripheral_location: str | None = Field(default=None, alias="Central vs peripheral location", description="ID 123")
    public_transport_access: str | None = Field(default=None, alias="Public transport access", description="ID 124")
    cab_availability_and_company_cab_policy: str | None = Field(default=None, alias="Cab availability and company cab policy", description="ID 125")
    commute_time_from_airport: str | None = Field(default=None, alias="Commute time from airport", description="ID 126")
    office_zone_type: str | None = Field(default=None, alias="Office zone type", description="ID 127")
    area_safety: str | None = Field(default=None, alias="Area safety", description="ID 128")
    company_safety_policies: str | None = Field(default=None, alias="Company safety policies", description="ID 129")
    office_infrastructure_safety: str | None = Field(default=None, alias="Office infrastructure safety", description="ID 130")
    emergency_response_preparedness: str | None = Field(default=None, alias="Emergency response preparedness", description="ID 131")
    health_support: str | None = Field(default=None, alias="Health support", description="ID 132")
    onboarding_and_training_quality: str | None = Field(default=None, alias="Onboarding and training quality", description="ID 133")
    learning_culture: str | None = Field(default=None, alias="Learning culture", description="ID 134")
    exposure_quality: str | None = Field(default=None, alias="Exposure quality", description="ID 135")
    mentorship_availability: str | None = Field(default=None, alias="Mentorship availability", description="ID 136")
    internal_mobility: str | None = Field(default=None, alias="Internal mobility", description="ID 137")
    promotion_clarity: str | None = Field(default=None, alias="Promotion clarity", description="ID 138")
    tools_and_technology_access: str | None = Field(default=None, alias="Tools and technology access", description="ID 139")
    role_clarity: str | None = Field(default=None, alias="Role clarity", description="ID 140")
    early_ownership: str | None = Field(default=None, alias="Early ownership", description="ID 141")
    work_impact: str | None = Field(default=None, alias="Work impact", description="ID 142")
    execution_vs_thinking_balance: str | None = Field(default=None, alias="Execution vs thinking balance", description="ID 143")
    automation_level: str | None = Field(default=None, alias="Automation level", description="ID 144")
    cross_functional_exposure: str | None = Field(default=None, alias="Cross-functional exposure", description="ID 145")
    company_maturity: str | None = Field(default=None, alias="Company maturity", description="ID 146")
    brand_value: str | None = Field(default=None, alias="Brand value", description="ID 147")
    client_quality: str | None = Field(default=None, alias="Client quality", description="ID 148")
    layoff_history: str | None = Field(default=None, alias="Layoff history", description="ID 149")
    fixed_vs_variable_pay: str | None = Field(default=None, alias="Fixed vs variable pay", description="ID 150")
    bonus_predictability: str | None = Field(default=None, alias="Bonus predictability", description="ID 151")
    esops_and_long_term_incentives: str | None = Field(default=None, alias="ESOPs and long-term incentives", description="ID 152")
    family_health_insurance: str | None = Field(default=None, alias="Family health insurance", description="ID 153")
    relocation_support: str | None = Field(default=None, alias="Relocation support", description="ID 154")
    lifestyle_and_wellness_benefits: str | None = Field(default=None, alias="Lifestyle and wellness benefits", description="ID 155")
    exit_opportunities: str | None = Field(default=None, alias="Exit opportunities", description="ID 156")
    skill_relevance: str | None = Field(default=None, alias="Skill relevance", description="ID 157")
    external_recognition: str | None = Field(default=None, alias="External recognition", description="ID 158")
    network_strength: str | None = Field(default=None, alias="Network strength", description="ID 159")
    global_exposure: str | None = Field(default=None, alias="Global exposure", description="ID 160")
    mission_clarity: str | None = Field(default=None, alias="Mission clarity", description="ID 161")
    sustainability_and_csr: str | None = Field(default=None, alias="Sustainability and CSR", description="ID 162")
    crisis_behavior: str | None = Field(default=None, alias="Crisis behavior", description="ID 163")

    @model_validator(mode="after")
    def validate_with_schema(self) -> "Company163Model":
        errors: list[str] = []
        data = self.model_dump(by_alias=True)
        for col, meta in FIELD_META.items():
            value = data.get(col)
            if value is None:
                if meta["required"]:
                    errors.append(f"{col}: required value missing")
                continue
            s = str(value).strip()
            if meta["required"] and not s:
                errors.append(f"{col}: required value empty")
            dtype = (meta["data_type"] or "").upper()
            if "INTEGER" in dtype and s and not re.fullmatch(r"-?\d+", s):
                errors.append(f"{col}: integer expected")
            if "DECIMAL" in dtype and s and not re.fullmatch(r"-?\d+(?:\.\d+)?", s.replace(",", "")):
                errors.append(f"{col}: decimal expected")
            pattern = (meta["regex_pattern"] or "").strip().strip("`")
            if pattern and pattern not in {"[]", "N/A"}:
                try:
                    if s and not re.match(pattern, s):
                        errors.append(f"{col}: regex mismatch")
                except re.error:
                    pass
        if errors:
            raise ValueError("; ".join(errors[:50]))
        return self


FIELD_META: dict[str, dict[str, Any]] = {
    "Company Name": {"id": 1, "required": True, "data_type": "VARCHAR(255)", "regex_pattern": "^[\\w\\s&.,\\-\\(\\)'\\u00C0-\\u017F]+$"},
    "Short Name": {"id": 2, "required": False, "data_type": "VARCHAR(100)", "regex_pattern": "^[\\w\\s&.\\-]+$"},
    "Logo": {"id": 3, "required": True, "data_type": "TEXT (URL)", "regex_pattern": "^https?:\\/\\/.*\\.(?:png|jpg|jpeg|svg|webp)(?:\\?.*)?$"},
    "Category": {"id": 4, "required": True, "data_type": "VARCHAR(50)", "regex_pattern": "^(Startup|MSME|SMB|Enterprise|Investor|VC|Conglomerate)$"},
    "Year of Incorporation": {"id": 5, "required": True, "data_type": "INTEGER", "regex_pattern": "^(19|20)"},
    "Overview of the Company": {"id": 6, "required": True, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Nature of Company": {"id": 7, "required": True, "data_type": "VARCHAR(50)", "regex_pattern": "^(Private|Public|Subsidiary|Partnership|Non-Profit|Govt)$"},
    "Company Headquarters": {"id": 8, "required": True, "data_type": "VARCHAR(255)", "regex_pattern": "^[\\w\\s,.\\-]+$"},
    "Countries Operating In": {"id": 9, "required": False, "data_type": "TEXT", "regex_pattern": "^([A-Za-z\\s]+)(,\\s*[A-Za-z\\s]+)*$"},
    "Number of Offices (beyond HQ)": {"id": 10, "required": False, "data_type": "INTEGER", "regex_pattern": "^\\d+$"},
    "Office Locations": {"id": 11, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Employee Size": {"id": 12, "required": True, "data_type": "VARCHAR(50)", "regex_pattern": "^(\\d+|\\d+-\\d+)$"},
    "Hiring Velocity": {"id": 13, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Employee Turnover": {"id": 14, "required": False, "data_type": "VARCHAR(10)", "regex_pattern": "^\\d{1,3}(\\.\\d{1,2})?%$"},
    "Average Retention Tenure": {"id": 15, "required": False, "data_type": "VARCHAR(20)", "regex_pattern": "^\\d+(\\.\\d+)?\\s?(Years?|Months?)$"},
    "Pain Points Being Addressed": {"id": 16, "required": True, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Focus Sectors / Industries": {"id": 17, "required": True, "data_type": "VARCHAR(500)", "regex_pattern": "^[\\w\\s&.,\\-/]+$"},
    "Services / Offerings / Products": {"id": 18, "required": True, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Top Customers by Client Segments": {"id": 19, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Core Value Proposition": {"id": 20, "required": True, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Vision": {"id": 21, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Mission": {"id": 22, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Values": {"id": 23, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Unique Differentiators": {"id": 24, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Competitive Advantages": {"id": 25, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Weaknesses / Gaps in Offering": {"id": 26, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Key Challenges and Unmet Needs": {"id": 27, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Key Competitors": {"id": 28, "required": True, "data_type": "TEXT", "regex_pattern": "^[\\w\\s&.,\\-/]+(,\\s*[\\w\\s&.,\\-/]+)*$"},
    "Technology Partners": {"id": 29, "required": False, "data_type": "TEXT", "regex_pattern": "^[\\w\\s&.,\\-/]+(,\\s*[\\w\\s&.,\\-/]+)*$"},
    "Interesting Facts": {"id": 30, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Recent News": {"id": 31, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Website URL": {"id": 32, "required": True, "data_type": "VARCHAR(500)", "regex_pattern": "^https?:\\/\\/(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b([-a-zA-Z0-9()@:%_\\+.~#?&//=]*)$"},
    "Quality of Website": {"id": 33, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Website Rating": {"id": 34, "required": False, "data_type": "DECIMAL(3,1)", "regex_pattern": "^(10(\\.0)?|[0-9](\\.\\d)?)$"},
    "Website Traffic Rank": {"id": 35, "required": False, "data_type": "INTEGER", "regex_pattern": "^\\d+$"},
    "Social Media Followers – Combined": {"id": 36, "required": True, "data_type": "INTEGER", "regex_pattern": "^\\d+$"},
    "Glassdoor Rating": {"id": 37, "required": False, "data_type": "DECIMAL(2,1)", "regex_pattern": "^[1-5](\\.\\d)?$"},
    "Indeed Rating": {"id": 38, "required": False, "data_type": "DECIMAL(2,1)", "regex_pattern": "^[1-5](\\.\\d)?$"},
    "Google Reviews Rating": {"id": 39, "required": False, "data_type": "DECIMAL(2,1)", "regex_pattern": "^[1-5](\\.\\d)?$"},
    "LinkedIn Profile URL": {"id": 40, "required": False, "data_type": "VARCHAR(500)", "regex_pattern": "^https?:\\/\\/(www\\.)?linkedin\\.com\\/company\\/[A-Za-z0-9_\\-]+\\/?$"},
    "Twitter (X) Handle": {"id": 41, "required": False, "data_type": "VARCHAR(30)", "regex_pattern": "^@?[A-Za-z0-9_]{1,15}$"},
    "Facebook Page URL": {"id": 42, "required": False, "data_type": "VARCHAR(500)", "regex_pattern": "^https?:\\/\\/(www\\.)?facebook\\.com\\/[A-Za-z0-9_\\.\\-]+\\/?$"},
    "Instagram Page URL": {"id": 43, "required": False, "data_type": "VARCHAR(500)", "regex_pattern": "^https?:\\/\\/(www\\.)?instagram\\.com\\/[A-Za-z0-9_\\.\\-]+\\/?$"},
    "CEO Name": {"id": 44, "required": True, "data_type": "VARCHAR(100)", "regex_pattern": "^[A-Za-z-–˜-¸-¿\\s.\\-']+$"},
    "CEO LinkedIn URL": {"id": 45, "required": False, "data_type": "VARCHAR(500)", "regex_pattern": "^https?:\\/\\/(www\\.)?linkedin\\.com\\/in\\/[A-Za-z0-9_\\-]+\\/?$"},
    "Key Business Leaders": {"id": 46, "required": True, "data_type": "JSON", "regex_pattern": "[\\s\\S]*"},
    "Warm Introduction Pathways": {"id": 47, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Decision Maker Accessibility": {"id": 48, "required": False, "data_type": "VARCHAR(250)", "regex_pattern": "^(High|Medium|Low).*$"},
    "Company Contact Email": {"id": 49, "required": False, "data_type": "VARCHAR(255)", "regex_pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
    "Company Phone Number": {"id": 50, "required": False, "data_type": "VARCHAR(20)", "regex_pattern": "^\\+?[1-9]\\d{1,14}$"},
    "Primary Contact Person's Name": {"id": 51, "required": False, "data_type": "VARCHAR(100)", "regex_pattern": "^[A-Za-z\\s.\\-']+$"},
    "Primary Contact Person's Title": {"id": 52, "required": False, "data_type": "VARCHAR(100)", "regex_pattern": "^[\\w\\s&.\\-]+$"},
    "Primary Contact Person's Email": {"id": 53, "required": False, "data_type": "VARCHAR(255)", "regex_pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
    "Primary Contact Person's Phone Number": {"id": 54, "required": False, "data_type": "VARCHAR(20)", "regex_pattern": "^\\+?[1-9]\\d{1,14}$"},
    "Awards & Recognitions": {"id": 55, "required": False, "data_type": "TEXT", "regex_pattern": "^[\\s\\S]*$"},
    "Brand Sentiment Score": {"id": 56, "required": False, "data_type": "VARCHAR(100)", "regex_pattern": "^(Positive|Neutral|Negative)$|^\\d{1,3}$"},
    "Event Participation": {"id": 57, "required": False, "data_type": "TEXT", "regex_pattern": "^[\\s\\S]*$"},
    "Regulatory & Compliance Status": {"id": 58, "required": False, "data_type": "VARCHAR(500)", "regex_pattern": "^(SOC2|HIPAA|GDPR|ISO27001|PCI-DSS).*$"},
    "Legal Issues / Controversies": {"id": 59, "required": False, "data_type": "TEXT", "regex_pattern": "`^(N/A"},
    "Annual Revenues": {"id": 60, "required": False, "data_type": "DECIMAL / VARCHAR", "regex_pattern": "`^$?(?:\\d{1,3}(?:,\\d{3})+"},
    "Annual Profits": {"id": 61, "required": False, "data_type": "DECIMAL", "regex_pattern": "`^-?$?(?:\\d{1,3}(?:,\\d{3})+"},
    "Revenue Mix": {"id": 62, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^\\d{1,3}%?\\s?\\/\\s?\\d{1,3}%?$"},
    "Company Valuation": {"id": 63, "required": False, "data_type": "DECIMAL", "regex_pattern": "^\\$?[\\d,]+(\\.\\d{2})?[KkMmBb]?$"},
    "Year-over-Year Growth Rate": {"id": 64, "required": False, "data_type": "VARCHAR(10)", "regex_pattern": "^[+-]?\\d{1,3}(\\.\\d{1,2})?%$"},
    "Profitability Status": {"id": 65, "required": True, "data_type": "VARCHAR(20)", "regex_pattern": "^(Profitable|Break-even|Loss-making)$"},
    "Market Share (%)": {"id": 66, "required": False, "data_type": "VARCHAR(10)", "regex_pattern": "^\\d{1,3}(\\.\\d{1,2})?%$"},
    "Key Investors / Backers": {"id": 67, "required": False, "data_type": "TEXT", "regex_pattern": "^[\\w\\s&.,\\-\\(\\)]+(,\\s*[\\w\\s&.,\\-\\(\\)]+)*$"},
    "Recent Funding Rounds": {"id": 68, "required": False, "data_type": "TEXT", "regex_pattern": "^(\\d{4}-\\d{2}-\\d{2}\\s-\\s\\$?\\d+(?:\\.\\d{2})?)(,\\s*\\d{4}-\\d{2}-\\d{2}\\s-\\s\\$?\\d+(?:\\.\\d{2})?)*$"},
    "Total Capital Raised": {"id": 69, "required": False, "data_type": "DECIMAL", "regex_pattern": "^\\$?[\\d,]+(\\.\\d{2})?[KkMmBb]?$"},
    "ESG Practices or Ratings": {"id": 70, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Sales Motion": {"id": 71, "required": True, "data_type": "VARCHAR(100)", "regex_pattern": "^(PLG|Product-Led|Sales-Led|Field Sales|Channel|Hybrid).*$"},
    "Customer Acquisition Cost (CAC)": {"id": 72, "required": False, "data_type": "DECIMAL", "regex_pattern": "^\\$?[\\d,]+(\\.\\d{2})?$"},
    "Customer Lifetime Value (CLV)": {"id": 73, "required": False, "data_type": "DECIMAL", "regex_pattern": "^\\$?[\\d,]+(\\.\\d{2})?$"},
    "CAC:LTV Ratio": {"id": 74, "required": False, "data_type": "VARCHAR(10)", "regex_pattern": "^\\d+(\\.\\d+)?(:\\d+)?$"},
    "Churn Rate": {"id": 75, "required": False, "data_type": "VARCHAR(10)", "regex_pattern": "^(100(\\.0{1,2})?|(\\d{1,2})(\\.\\d{1,2})?)%$"},
    "Net Promoter Score (NPS)": {"id": 76, "required": False, "data_type": "INTEGER", "regex_pattern": "^-?(100|[1-9]\\d?|0)$"},
    "Customer Concentration Risk": {"id": 77, "required": False, "data_type": "TEXT", "regex_pattern": "^(Yes|No|High|Low).*$"},
    "Burn Rate": {"id": 78, "required": False, "data_type": "DECIMAL", "regex_pattern": "^\\$?\\d{1,3}(,\\d{3})*(\\.\\d{2})?[KkMmBb]?$"},
    "Runway": {"id": 79, "required": False, "data_type": "DECIMAL", "regex_pattern": "^\\d+(\\.\\d+)?$"},
    "Burn Multiplier": {"id": 80, "required": False, "data_type": "DECIMAL", "regex_pattern": "^\\d+(\\.\\d+)?$"},
    "Intellectual Property": {"id": 81, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "R&D Investment": {"id": 82, "required": False, "data_type": "VARCHAR(20)", "regex_pattern": "^\\$?[\\d,]+(\\.\\d{2})?[KkMmBb]?$"},
    "AI/ML Adoption Level": {"id": 83, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Tech Stack/Tools Used": {"id": 84, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Cybersecurity Posture": {"id": 85, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Supply Chain Dependencies": {"id": 86, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Geopolitical Risks": {"id": 87, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Macro Risks": {"id": 88, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Diversity Metrics": {"id": 89, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Remote Work Policy": {"id": 90, "required": True, "data_type": "VARCHAR(100)", "regex_pattern": "^(Remote|Hybrid|On-Site|Office-First).*$"},
    "Training/Development Spend": {"id": 91, "required": False, "data_type": "VARCHAR(20)", "regex_pattern": "^\\$?[\\d,]+(\\.\\d{2})?(\\s?\\/|\\s?per)?.*$"},
    "Partnership Ecosystem": {"id": 92, "required": False, "data_type": "TEXT", "regex_pattern": "^[A-Za-z0-9 &.-]+(,\\s*[A-Za-z0-9 &.-]+)*$"},
    "Exit Strategy/History": {"id": 93, "required": False, "data_type": "TEXT", "regex_pattern": "(?i).*(IPO|Acquisition).*"},
    "Carbon Footprint/Environmental Impact": {"id": 94, "required": False, "data_type": "VARCHAR(500)", "regex_pattern": "^[\\d\\.]+\\s?CO2e$"},
    "Ethical Sourcing Practices": {"id": 95, "required": False, "data_type": "TEXT", "regex_pattern": "(?i).*(Fair Trade|Conflict-free).*"},
    "Benchmark vs. Peers": {"id": 96, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Future Projections": {"id": 97, "required": False, "data_type": "TEXT", "regex_pattern": "(?i)[\\s\\S]*(202[6-9]|20[3-9][0-9]|Q[1-4])[\\s\\S]*"},
    "Strategic Priorities": {"id": 98, "required": True, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Industry Associations / Memberships": {"id": 99, "required": False, "data_type": "TEXT", "regex_pattern": "^[^,]+(?:,\\s*[^,]+)*$"},
    "Case Studies / Public Success Stories": {"id": 100, "required": False, "data_type": "TEXT", "regex_pattern": "^.+ - https?:\\/\\/.+ - .+$"},
    "Go-to-Market Strategy": {"id": 101, "required": True, "data_type": "TEXT", "regex_pattern": "(?i)[\\s\\S]*(plg|direct|channel)[\\s\\S]*"},
    "Innovation Roadmap": {"id": 102, "required": False, "data_type": "TEXT", "regex_pattern": "(?i)[\\s\\S]*(202[6-9]|20[3-9][0-9]|Q[1-4])[\\s\\S]*"},
    "Product Pipeline": {"id": 103, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Board of Directors / Advisors": {"id": 104, "required": True, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Company Introduction / Marketing videos": {"id": 105, "required": False, "data_type": "TEXT", "regex_pattern": "^https?:\\/\\/(www\\.)?(youtube\\.com|vimeo\\.com|youtu\\.be)\\/.*$"},
    "Customer testimonial": {"id": 106, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Industry Benchmark Technology Adoption Rating": {"id": 107, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^([1-9]|10)|(Leader|Challenger|Laggard)$"},
    "Total Addressable Market (TAM)": {"id": 108, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^\\$?[\\d,]+(\\.\\d{2})?[KkMmBbTt]?$"},
    "Serviceable Addressable Market (SAM)": {"id": 109, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^\\$?[\\d,]+(\\.\\d{2})?[KkMmBbTt]?$"},
    "Serviceable Obtainable Market (SOM)": {"id": 110, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^\\$?[\\d,]+(\\.\\d{2})?[KkMmBbTt]?$"},
    "Work culture": {"id": 111, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Manager quality": {"id": 112, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Psychological safety": {"id": 113, "required": False, "data_type": "VARCHAR(100)", "regex_pattern": "^(Low|Medium|High|Safe|Toxic).*$"},
    "Feedback culture": {"id": 114, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Diversity & inclusion": {"id": 115, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Ethical standards": {"id": 116, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Typical working hours": {"id": 117, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(\\d{1,2}(?::\\d{2})?\\s?(?:AM|PM|am|pm)?\\s?-\\s?\\d{1,2}(?::\\d{2})?\\s?(?:AM|PM|am|pm)?|Flexible|Fixed).*$"},
    "Overtime expectations": {"id": 118, "required": False, "data_type": "VARCHAR(100)", "regex_pattern": "^(Routine|Rare|Seasonal|Frequent|Occasional).*$"},
    "Weekend work": {"id": 119, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Never|Rarely|Occasionally|Frequently|Always).*$"},
    "Remote / hybrid / on-site flexibility": {"id": 120, "required": True, "data_type": "VARCHAR(50)", "regex_pattern": "^(Remote|Hybrid|On-Site|Flexible Choice).*$"},
    "Leave policy": {"id": 121, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Burnout risk": {"id": 122, "required": False, "data_type": "VARCHAR(20)", "regex_pattern": "^(Low|Medium|High|Severe).*$"},
    "Central vs peripheral location": {"id": 123, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Central|Peripheral|CBD|Suburbs|Remote).*$"},
    "Public transport access": {"id": 124, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Poor|Good|Excellent|Metro Connected|Bus only).*$"},
    "Cab availability and company cab policy": {"id": 125, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Commute time from airport": {"id": 126, "required": False, "data_type": "INTEGER", "regex_pattern": "^\\d+$"},
    "Office zone type": {"id": 127, "required": False, "data_type": "VARCHAR(100)", "regex_pattern": "^(Tech Park|SEZ|Commercial|Residential|Mixed).*$"},
    "Area safety": {"id": 128, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Safe|Moderate|Unsafe|High Crime).*$"},
    "Company safety policies": {"id": 129, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Office infrastructure safety": {"id": 130, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Compliant|Non-Compliant|Certified).*$"},
    "Emergency response preparedness": {"id": 131, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Health support": {"id": 132, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Onboarding and training quality": {"id": 133, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Poor|Average|Good|Structured|Ad-hoc).*$"},
    "Learning culture": {"id": 134, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Exposure quality": {"id": 135, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Mentorship availability": {"id": 136, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Formal Program|Informal|None|Limited).*$"},
    "Internal mobility": {"id": 137, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(High|Medium|Low|Frozen).*$"},
    "Promotion clarity": {"id": 138, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Tools and technology access": {"id": 139, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Role clarity": {"id": 140, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(High|Medium|Low|Vague|Defined).*$"},
    "Early ownership": {"id": 141, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(High|Low|Gradual|Immediate).*$"},
    "Work impact": {"id": 142, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(High|Medium|Low|Back-office|Front-line).*$"},
    "Execution vs thinking balance": {"id": 143, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Execution-heavy|Balanced|Strategy-focused).*$"},
    "Automation level": {"id": 144, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(High|Medium|Low|Manual|Automated).*$"},
    "Cross-functional exposure": {"id": 145, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Siloed|Collaborative|Matrix|Cross-functional).*$"},
    "Company maturity": {"id": 146, "required": True, "data_type": "VARCHAR(50)", "regex_pattern": "^(Startup|Scale-up|Mature|Enterprise|Declining).*$"},
    "Brand value": {"id": 147, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Tier 1|Tier 2|Tier 3|Unkown|Unicorn).*$"},
    "Client quality": {"id": 148, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Fortune 500|Enterprise|SMB|Mid-market).*$"},
    "Layoff history": {"id": 149, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Fixed vs variable pay": {"id": 150, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(\\d{1,3}:\\d{1,3}|Fixed Only|Variable Heavy).*$"},
    "Bonus predictability": {"id": 151, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Guaranteed|Performance-linked|Discretionary|Unpredictable).*$"},
    "ESOPs and long-term incentives": {"id": 152, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Family health insurance": {"id": 153, "required": False, "data_type": "VARCHAR(500)", "regex_pattern": "[\\s\\S]*"},
    "Relocation support": {"id": 154, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Lifestyle and wellness benefits": {"id": 155, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Exit opportunities": {"id": 156, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Skill relevance": {"id": 157, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(High|Medium|Low|Niche|Legacy).*$"},
    "External recognition": {"id": 158, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(High|Medium|Low|Global|Unknown).*$"},
    "Network strength": {"id": 159, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Strong|Weak|Moderate|Mafia).*$"},
    "Global exposure": {"id": 160, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Yes|No|Limited).*$"},
    "Mission clarity": {"id": 161, "required": False, "data_type": "VARCHAR(50)", "regex_pattern": "^(Clear|Confusing|Generic|Inspiring).*$"},
    "Sustainability and CSR": {"id": 162, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
    "Crisis behavior": {"id": 163, "required": False, "data_type": "TEXT", "regex_pattern": "[\\s\\S]*"},
}
