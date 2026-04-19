from .pubmed import PubMedClient
from .openalex import OpenAlexClient
from .clinical_trials import ClinicalTrialsClient
from .europepmc import EuropePMCClient
from .unpaywall import UnpaywallClient
from .semantic_scholar import SemanticScholarClient
from .calculations import SportsCalc
from .exporter import ResearchExporter
from .supplements import SUPPLEMENT_DB, resolve_supplement
from .interactions import INTERACTION_DB, lookup_interactions
from .biomarkers import BIOMARKER_DB, BiomarkerInterpreter
from .grade import assess as grade_assess
from .quality_assessment import get_checklist
from .auto_quality import auto_assess
from .effect_size import cohens_d, hedges_g
from .pdf_export import generate_client_report
from .pdf_reader import read_pdf
from .cost_tracker import SessionCostTracker
from .team_analytics import format_team_summary
from .proactive import check_biomarker
from .contradiction import detect_contradictions
from .command_router import route_natural_language
from .protocol_templates import get_template, list_templates
from .nutrient_gaps import analyze_gaps
from .knowledge_frontier import analyze_frontiers
from .freshness import format_freshness_report
from .timing_schedule import generate_timing_schedule
from .client_export import export_client
from .config import load_config
from .injury_prevention import (
    calculate_acwr,
    score_fms_movement,
    calculate_fms_composite,
    screen_overuse_risk,
    get_prevention_protocol,
    match_prevention_protocol,
    return_to_sport_decision,
    list_prevention_protocols,
    PROTOCOL_DB,
)
from .female_athlete import (
    get_cycle_phase,
    match_training_to_phase,
    screen_reds,
    postpartum_return_protocol,
    calculate_iron_needs,
    CYCLE_PHASES,
)
from .environmental import (
    altitude_training_protocol,
    heat_acclimatization_protocol,
    air_quality_adjustment,
    cold_exposure_protocol,
    jet_lag_protocol,
    WBGT_CATEGORIES,
    AQI_CATEGORIES,
)
from .mental_performance import (
    assess_competition_anxiety,
    assess_mental_fatigue,
    assess_burnout,
    get_visualization_protocol,
    list_visualization_protocols,
    generate_pre_competition_routine,
    VISUALIZATION_DB,
)

__all__ = [
    "PubMedClient", "OpenAlexClient", "ClinicalTrialsClient",
    "EuropePMCClient", "UnpaywallClient", "SemanticScholarClient",
    "SportsCalc", "ResearchExporter",
    "SUPPLEMENT_DB", "resolve_supplement", "INTERACTION_DB", "lookup_interactions",
    "BIOMARKER_DB", "BiomarkerInterpreter",
    "grade_assess", "get_checklist", "auto_assess",
    "cohens_d", "hedges_g",
    "generate_client_report", "read_pdf",
    "SessionCostTracker", "format_team_summary",
    "check_biomarker", "detect_contradictions",
    "route_natural_language", "get_template", "list_templates",
    "analyze_gaps", "analyze_frontiers", "format_freshness_report",
    "generate_timing_schedule", "export_client", "load_config",
    "calculate_acwr", "score_fms_movement", "calculate_fms_composite",
    "screen_overuse_risk", "get_prevention_protocol", "match_prevention_protocol",
    "return_to_sport_decision", "list_prevention_protocols", "PROTOCOL_DB",
    "get_cycle_phase", "match_training_to_phase", "screen_reds",
    "postpartum_return_protocol", "calculate_iron_needs", "CYCLE_PHASES",
    "altitude_training_protocol", "heat_acclimatization_protocol",
    "air_quality_adjustment", "cold_exposure_protocol", "jet_lag_protocol",
    "WBGT_CATEGORIES", "AQI_CATEGORIES",
    "assess_competition_anxiety", "assess_mental_fatigue", "assess_burnout",
    "get_visualization_protocol", "list_visualization_protocols",
    "generate_pre_competition_routine", "VISUALIZATION_DB",
]
