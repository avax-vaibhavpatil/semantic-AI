"""
Async Report Repository

Implements ReportRepository using the async database executor.
Assumes PostgreSQL with a table `analytics_llm.saved_reports`.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.models import Report
from app.core.constants import (
    REPORT_STATUS_ACTIVE,
    REPORT_STATUS_ARCHIVED,
    REPORT_STATUS_DELETED,
    MAX_TAGS_PER_REPORT,
)
from app.repositories.base import ReportRepository
from app.infrastructure.database.connection import get_async_engine
from app.infrastructure.database.query_executor import (
    execute_query_with_session,
    execute_query,
)


def _row_to_report(row: dict) -> Report:
    """Convert DB row dict to Report domain model."""
    return Report(
        report_id=row["report_id"],
        report_name=row["report_name"],
        user_question=row["user_question"],
        generated_sql=row["generated_sql"],
        user_id=row["user_id"],
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
        last_executed_at=row.get("last_executed_at"),
        execution_count=row.get("execution_count", 0),
        is_favorite=row.get("is_favorite", False),
        report_description=row.get("report_description"),
        tags=row.get("tags") or [],
        status=row.get("status", REPORT_STATUS_ACTIVE),
    )


class AsyncReportRepository(ReportRepository):
    """Async implementation of ReportRepository."""

    def __init__(
        self,
        engine: Optional[AsyncEngine] = None,
        schema: str = "analytics_llm",
        table: str = "saved_reports",
    ):
        self.engine = engine or get_async_engine()
        self.schema = schema
        self.table = table
        self.table_full = f"{self.schema}.{self.table}" if self.schema else self.table

    # --------------------------------------------------------------------- #
    # CREATE
    # --------------------------------------------------------------------- #
    async def save_report(self, report: Report) -> int:
        query = text(
            f"""
            INSERT INTO {self.table_full}
                (user_id, report_name, report_description, user_question, generated_sql,
                 tags, status, is_favorite, execution_count)
            VALUES
                (:user_id, :report_name, :report_description, :user_question, :generated_sql,
                 :tags, :status, :is_favorite, :execution_count)
            RETURNING report_id;
            """
        )

        async with self.engine.begin() as conn:
            result = await conn.execute(
                query,
                {
                    "user_id": report.user_id,
                    "report_name": report.report_name,
                    "report_description": report.report_description,
                    "user_question": report.user_question,
                    "generated_sql": report.generated_sql,
                    "tags": report.tags[:MAX_TAGS_PER_REPORT] if report.tags else [],
                    "status": report.status,
                    "is_favorite": report.is_favorite,
                    "execution_count": report.execution_count,
                },
            )
            report_id = result.scalar_one()
            return report_id

    # --------------------------------------------------------------------- #
    # READ
    # --------------------------------------------------------------------- #
    async def get_report(self, report_id: int, user_id: str) -> Optional[Report]:
        rows = await execute_query(
            f"""
            SELECT *
            FROM {self.table_full}
            WHERE report_id = :report_id AND user_id = :user_id AND status != :deleted
            """,
            engine=self.engine,
            max_rows=1,
        )
        if not rows:
            return None
        return _row_to_report(rows[0])

    async def list_reports(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[Report], int]:
        rows = await execute_query(
            f"""
            SELECT *
            FROM {self.table_full}
            WHERE user_id = :user_id AND status != :deleted
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """,
            engine=self.engine,
            max_rows=limit,
        )
        reports = [_row_to_report(r) for r in rows]

        total_rows = await execute_query(
            f"""
            SELECT COUNT(*) as total
            FROM {self.table_full}
            WHERE user_id = :user_id AND status != :deleted
            """,
            engine=self.engine,
            max_rows=1,
        )
        total = total_rows[0]["total"] if total_rows else 0
        return reports, total

    async def search_reports(
        self, user_id: str, query: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[Report], int]:
        rows = await execute_query(
            f"""
            SELECT *
            FROM {self.table_full}
            WHERE user_id = :user_id
              AND status != :deleted
              AND (
                    report_name ILIKE :q
                 OR user_question ILIKE :q
                 OR COALESCE(report_description, '') ILIKE :q
              )
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """,
            engine=self.engine,
            max_rows=limit,
        )
        reports = [_row_to_report(r) for r in rows]

        total_rows = await execute_query(
            f"""
            SELECT COUNT(*) as total
            FROM {self.table_full}
            WHERE user_id = :user_id
              AND status != :deleted
              AND (
                    report_name ILIKE :q
                 OR user_question ILIKE :q
                 OR COALESCE(report_description, '') ILIKE :q
              )
            """,
            engine=self.engine,
            max_rows=1,
        )
        total = total_rows[0]["total"] if total_rows else 0
        return reports, total

    # --------------------------------------------------------------------- #
    # UPDATE
    # --------------------------------------------------------------------- #
    async def update_report(
        self, report_id: int, user_id: str, updated: Report
    ) -> bool:
        query = text(
            f"""
            UPDATE {self.table_full}
            SET
                report_name = :report_name,
                report_description = :report_description,
                tags = :tags,
                is_favorite = :is_favorite,
                status = :status,
                updated_at = :updated_at
            WHERE report_id = :report_id AND user_id = :user_id AND status != :deleted
            """
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(
                query,
                {
                    "report_name": updated.report_name,
                    "report_description": updated.report_description,
                    "tags": updated.tags[:MAX_TAGS_PER_REPORT] if updated.tags else [],
                    "is_favorite": updated.is_favorite,
                    "status": updated.status,
                    "updated_at": datetime.utcnow(),
                    "report_id": report_id,
                    "user_id": user_id,
                },
            )
            return result.rowcount > 0

    # --------------------------------------------------------------------- #
    # DELETE (soft)
    # --------------------------------------------------------------------- #
    async def delete_report(self, report_id: int, user_id: str) -> bool:
        query = text(
            f"""
            UPDATE {self.table_full}
            SET status = :deleted, updated_at = :updated_at
            WHERE report_id = :report_id AND user_id = :user_id AND status != :deleted
            """
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(
                query,
                {
                    "deleted": REPORT_STATUS_DELETED,
                    "updated_at": datetime.utcnow(),
                    "report_id": report_id,
                    "user_id": user_id,
                },
            )
            return result.rowcount > 0

    # --------------------------------------------------------------------- #
    # EXECUTE SAVED SQL
    # --------------------------------------------------------------------- #
    async def execute_saved_sql(
        self, report_id: int, user_id: str, max_rows: int = 500
    ) -> (Report, List[dict]):
        report = await self.get_report(report_id, user_id)
        if not report:
            return None, []

        rows = await execute_query(
            report.generated_sql,
            engine=self.engine,
            max_rows=max_rows,
        )
        return report, rows

