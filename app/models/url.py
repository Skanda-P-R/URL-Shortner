from sqlalchemy import BigInteger, Column, DateTime, String, Text, func
from app.core.database import Base


class URLItem(Base):
    """
    SQLAlchemy Model for shortened URLs.

    - id: Unique, non-sequential 63-bit integer.
    - original_url: Unique long URL (enforces deduplication).
    - short_code: Base62-encoded representation of id, with unique index for rapid lookups.
    """
    __tablename__ = "urls"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
        doc="Non-sequential cryptographically secure unique ID",
    )
    original_url = Column(
        Text,
        nullable=False,
        unique=True,
        index=True,
        doc="Original long URL; unique index enforces deduplication",
    )
    short_code = Column(
        String(16),
        nullable=False,
        unique=True,
        index=True,
        doc="Base62 encoded short code; unique index accelerates lookup",
    )
    click_count = Column(
        BigInteger,
        default=0,
        nullable=False,
        doc="Count of redirects through this short URL",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when short URL was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        doc="Timestamp when URL record was last modified",
    )

    def __repr__(self) -> str:
        return f"<URLItem id={self.id} short_code='{self.short_code}' original_url='{self.original_url[:30]}...'>"
