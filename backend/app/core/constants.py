"""
IdeaScope – Application-wide constants.
Owner: Member 2 (Sufiyaan Imran)
"""

# ── Roles ─────────────────────────────────────────────────────────────────────
ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"

# ── Account lockout ───────────────────────────────────────────────────────────
MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15

# ── Groups ────────────────────────────────────────────────────────────────────
DEFAULT_MAX_GROUP_SIZE = 4

# ── Worker / Jobs ─────────────────────────────────────────────────────────────
MAX_JOB_ATTEMPTS = 3

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_DONE = "done"
JOB_STATUS_FAILED = "failed"

JOB_TYPE_IMPORT_FILE = "import_file"
JOB_TYPE_PROCESS_ABSTRACT = "process_abstract"
JOB_TYPE_ANALYZE_PROPOSAL = "analyze_proposal"
JOB_TYPE_GENERATE_PROPOSAL = "generate_proposal"

VALID_JOB_TYPES = {
    JOB_TYPE_IMPORT_FILE,
    JOB_TYPE_PROCESS_ABSTRACT,
    JOB_TYPE_ANALYZE_PROPOSAL,
    JOB_TYPE_GENERATE_PROPOSAL,
}
