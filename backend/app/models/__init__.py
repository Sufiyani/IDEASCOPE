"""
IdeaScope – SQLAlchemy model registry.
Import all models here so Alembic autogenerate can discover them.
"""

# ── Member 2 models ──────────────────────────────────────────────────────────
from app.models.user import User  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.group import Group, GroupMember  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.sdg import SDG  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.job import Job  # noqa: F401

# ── Member 3 models (add imports here when ready) ────────────────────────────
# from app.models.import_batch import ImportBatch  # noqa: F401
# from app.models.past_project import PastProject  # noqa: F401
# from app.models.proposal import Proposal  # noqa: F401
# from app.models.document import Document  # noqa: F401
# from app.models.final_scope import FinalScope, FinalScopeSDG  # noqa: F401
# from app.models.quota import Quota  # noqa: F401
# from app.models.setting import Setting  # noqa: F401

# ── Member 1 models (add imports here when ready) ────────────────────────────
# from app.models.past_project_feature import PastProjectFeature  # noqa: F401
# from app.models.analysis import Analysis  # noqa: F401
# from app.models.similar_match import SimilarMatch  # noqa: F401
# from app.models.suggestion import Suggestion  # noqa: F401
# from app.models.llm_usage import LLMUsage  # noqa: F401
