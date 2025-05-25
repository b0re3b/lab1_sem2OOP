from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from .base import BaseModel


class OperationLog(BaseModel):
    """Operation log model for audit trail"""

    __tablename__ = 'operation_logs'

    user_id = Column(Integer, ForeignKey('users.id'))
    operation_type = Column(String(50), nullable=False)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer)
    old_values = Column(JSON)
    new_values = Column(JSON)
    description = Column(Text)
    ip_address = Column(INET)
    user_agent = Column(Text)

    # Relationships
    user = relationship("User", back_populates="operation_logs")

    @property
    def operation_summary(self):
        """Get operation summary"""
        return f"{self.operation_type} on {self.table_name}(id={self.record_id})"

    def __repr__(self):
        return f"<OperationLog(operation='{self.operation_summary}', user_id={self.user_id})>"