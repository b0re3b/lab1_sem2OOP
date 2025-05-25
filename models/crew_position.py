from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .crew_member import CrewMember


@dataclass
class CrewPosition(Base):

    __tablename__ = "crew_positions"
    __table_args__ = {"schema": "airline"}

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Position details
    position_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        nullable=False
    )

    # Relationships
    crew_members: Mapped[List["CrewMember"]] = relationship(
        "CrewMember",
        back_populates="position",
        cascade="all, delete-orphan"
    )

    @property
    def member_count(self) -> int:
        """Count of crew members in this position"""
        return len(self.crew_members)

    @property
    def available_member_count(self) -> int:
        """Count of available crew members in this position"""
        return len([member for member in self.crew_members if member.is_available])

    def get_available_members(self) -> List["CrewMember"]:
        """Get list of available crew members for this position"""
        return [member for member in self.crew_members if member.is_available]

    def get_senior_members(self) -> List["CrewMember"]:
        """Get list of senior crew members for this position"""
        return [
            member for member in self.crew_members
            if member.certification_level in ["SENIOR", "CAPTAIN"]
        ]