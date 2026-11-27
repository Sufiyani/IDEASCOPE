"""
IdeaScope – SQLAlchemy model registry.
Import all models here so Alembic autogenerate can discover them.
"""

# ── Member 2 models ──────────────────────────────────────────────────────────
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.group import Group, GroupMember  # noqa: F401
from app.models.job import Job  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.sdg import SDG  # noqa: F401
from app.models.user import User  # noqa: F401

# ── Member 3 models (add imports here when ready) ────────────────────────────
# from app.models.import_batch import ImportBatch
# from app.models.past_project import PastProject
# from app.models.proposal import Proposal
# from app.models.document import Document
# from app.models.final_scope import FinalScope, FinalScopeSDG
# from app.models.quota import Quota
# from app.models.setting import Setting

# ── Member 1 models (add imports here when ready) ────────────────────────────
# from app.models.past_project_feature import PastProjectFeature
# from app.models.analysis import Analysis
# from app.models.similar_match import SimilarMatch
# from app.models.suggestion import Suggestion
# from app.models.llm_usage import LLMUsage
