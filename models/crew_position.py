from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel


class CrewPosition(BaseModel):
    """Crew position model for different crew roles"""

    __tablename__ = 'crew_positions'

    position_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_required = Column(Boolean, default=True, nullable=False)

    # Relationships
    crew_members = relationship("CrewMember", back_populates="position")

    def __repr__(self):
        return f"<CrewPosition(name='{self.position_name}', required={self.is_required})>"
