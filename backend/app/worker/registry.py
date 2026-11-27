"""
IdeaScope – Job type to handler mapping.
Owner: Member 2 (Sufiyaan Imran)

Handlers are imported lazily so a missing module never crashes the worker
at startup – the job simply fails with 'no_handler_registered'.
Handler signature: handle_xxx(db: Session, job: Job) -> None
"""

from __future__ import annotations

from collections.abc import Callable


def get_handler(job_type: str) -> Callable | None:
    """
    Return the handler callable for the given job_type, or None.
    Imports are lazy – if the module does not exist yet, returns None.
    """
    if job_type == "import_file":
        try:
            from app.ingestion.excel_import import handle_import_file

            return handle_import_file
        except (ImportError, AttributeError):
            return None

    if job_type == "process_abstract":
        try:
            from app.ai.pipelines import handle_process_abstract

            return handle_process_abstract
        except (ImportError, AttributeError):
            return None

    if job_type == "analyze_proposal":
        try:
            from app.ai.pipelines import handle_analyze_proposal

            return handle_analyze_proposal
        except (ImportError, AttributeError):
            return None

    if job_type == "generate_proposal":
        try:
            from app.ai.pipelines import handle_generate_proposal

            return handle_generate_proposal
        except (ImportError, AttributeError):
            return None

    return None
