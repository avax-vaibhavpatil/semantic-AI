"""
Repository Interfaces (Async)

Defines the contracts for data access. Implementations will use the async
database executor, but services depend only on these interfaces.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.models import Report, SemanticLayer


class ReportRepository(ABC):
    """Async repository interface for reports."""

    @abstractmethod
    async def save_report(
        self,
        report: Report,
    ) -> int:
        """Persist a report and return its ID."""

    @abstractmethod
    async def get_report(self, report_id: int, user_id: str) -> Optional[Report]:
        """Fetch a report by ID for a given user."""

    @abstractmethod
    async def list_reports(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> (List[Report], int):
        """List reports for a user with total count."""

    @abstractmethod
    async def search_reports(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> (List[Report], int):
        """Search reports for a user with total count."""

    @abstractmethod
    async def update_report(
        self,
        report_id: int,
        user_id: str,
        updated: Report,
    ) -> bool:
        """Update a report; returns True if updated."""

    @abstractmethod
    async def delete_report(
        self,
        report_id: int,
        user_id: str,
    ) -> bool:
        """Soft-delete a report; returns True if deleted."""

    @abstractmethod
    async def execute_saved_sql(
        self,
        report_id: int,
        user_id: str,
        max_rows: int = 500,
    ) -> (Report, List[dict]):
        """Execute the saved SQL for a report and return metadata + rows."""


class SemanticRepository(ABC):
    """Repository interface for semantic layer loading."""

    @abstractmethod
    async def load_semantic(self) -> SemanticLayer:
        """Load semantic layer definition (e.g., from JSON file)."""

    @abstractmethod
    async def reload_semantic(self) -> SemanticLayer:
        """Reload semantic layer (useful if file changes)."""


