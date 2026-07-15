from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base — import all models here so Alembic autogenerate sees them."""


# Import models so they register with Base.metadata for Alembic autogeneration.
from app.models.user import User  # noqa: E402,F401
from app.models.document import Document, DocumentChunk  # noqa: E402,F401
from app.models.audit import AgentRun, AuditLog  # noqa: E402,F401
