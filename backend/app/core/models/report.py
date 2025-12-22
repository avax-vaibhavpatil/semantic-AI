"""
Report Domain Model

Represents a saved report in the system.
This is a pure domain model - no framework dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Report:
    """
    Represents a saved report
    
    A report is a saved query that users can execute repeatedly.
    """
    report_id: int
    report_name: str
    user_question: str
    generated_sql: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0
    is_favorite: bool = False
    report_description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: str = "active"
    
    def __post_init__(self):
        """Validate after initialization"""
        if not self.report_name or not self.report_name.strip():
            raise ValueError("Report name cannot be empty")
        if not self.user_question or not self.user_question.strip():
            raise ValueError("User question cannot be empty")
        if not self.generated_sql or not self.generated_sql.strip():
            raise ValueError("Generated SQL cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        if self.execution_count < 0:
            raise ValueError("Execution count cannot be negative")
        if self.status not in ["active", "archived", "deleted"]:
            raise ValueError(f"Invalid status: {self.status}")
    
    def mark_executed(self) -> None:
        """Mark report as executed (update timestamp and count)"""
        self.last_executed_at = datetime.utcnow()
        self.execution_count += 1
    
    def toggle_favorite(self) -> None:
        """Toggle favorite status"""
        self.is_favorite = not self.is_favorite
    
    def is_active(self) -> bool:
        """Check if report is active"""
        return self.status == "active"
    
    def archive(self) -> None:
        """Archive the report"""
        self.status = "archived"
    
    def delete(self) -> None:
        """Mark report as deleted (soft delete)"""
        self.status = "deleted"

