from sqlalchemy import Column, String, Integer, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum


class CertificationLevel(enum.Enum):
    """Certification levels for crew members"""
    JUNIOR = "JUNIOR"
    SENIOR = "SENIOR"
    CAPTAIN = "CAPTAIN"


class CrewMember(BaseModel):
    """Crew member model for flight crew"""

    __tablename__ = 'crew_members'

    employee_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    position_id = Column(Integer, ForeignKey('crew_positions.id'), nullable=False)
    experience_years = Column(Integer, default=0)
    certification_level = Column(Enum(CertificationLevel), default=CertificationLevel.JUNIOR)
    is_available = Column(Boolean, default=True, nullable=False)
    phone = Column(String(20))
    email = Column(String(255))

    # Relationships
    position = relationship("CrewPosition", back_populates="crew_members")
    flight_assignments = relationship("FlightAssignment", back_populates="crew_member")

    @property
    def full_name(self):
        """Get crew member's full name"""
        return f"{self.first_name} {self.last_name}"

    def is_captain(self):
        """Check if crew member is captain"""
        return self.certification_level == CertificationLevel.CAPTAIN

    def is_senior(self):
        """Check if crew member is senior level"""
        return self.certification_level in [CertificationLevel.SENIOR, CertificationLevel.CAPTAIN]

    def __repr__(self):
        return f"<CrewMember(employee_id='{self.employee_id}', name='{self.full_name}')>"