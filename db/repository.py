"""
Repository pattern for database operations.
Provides high-level interface for database access without raw queries.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from supabase import Client

from .models import Report, ReportCreate, ReportUpdate, ChatHistoryRecord, ChatMessageCreate

logger = logging.getLogger(__name__)


class ReportRepository:
    """
    Repository for managing report operations with Supabase.
    Provides async methods for CRUD operations on reports and related data.
    """

    def __init__(self, db: Client):
        """Initialize repository with Supabase client."""
        self.db = db
        self.reports_table = "reports"
        self.chat_history_table = "chat_history"
        self.users_table = "users"

    async def save_report(self, report_data: Dict[str, Any]) -> str:
        """
        Save a blood report analysis to the database.

        Args:
            report_data: Dictionary containing report information

        Returns:
            str: The report ID (UUID)

        Raises:
            ValueError: If save operation fails
        """
        try:
            report_id = str(uuid.uuid4())

            payload = {
                "id": report_id,
                "user_id": report_data.get("user_id"),
                "created_at": datetime.utcnow().isoformat(),
                "parameters": report_data.get("parameters", {}),
                "analysis": report_data.get("analysis", {}),
                "risks": report_data.get("risks", []),
                "recommendations": report_data.get("recommendations", []),
                "summary": report_data.get("summary", {}),
                "status": report_data.get("status", "completed"),
                "file_name": report_data.get("file_name"),
                "file_type": report_data.get("file_type"),
            }

            result = self.db.table(self.reports_table).insert(payload).execute()

            if result.data:
                logger.info(f"Report saved: {report_id}")
                return report_id
            else:
                raise ValueError(f"Failed to save report: {result.error}")

        except Exception as e:
            logger.error(f"Error saving report: {e}")
            raise ValueError(f"Database error while saving report: {str(e)}")

    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a report by ID.

        Args:
            report_id: UUID of the report to retrieve

        Returns:
            dict | None: Report data if found, None otherwise
        """
        try:
            result = (
                self.db.table(self.reports_table)
                .select("*")
                .eq("id", report_id)
                .single()
                .execute()
            )

            if result.data:
                logger.info(f"Report retrieved: {report_id}")
                return result.data
            else:
                logger.warning(f"Report not found: {report_id}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving report {report_id}: {e}")
            return None

    async def get_user_reports(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all reports for a specific user.

        Args:
            user_id: UUID of the user

        Returns:
            list[dict]: List of reports created by the user, ordered by creation date (newest first)
        """
        try:
            result = (
                self.db.table(self.reports_table)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

            if result.data:
                logger.info(f"Retrieved {len(result.data)} reports for user {user_id}")
                return result.data
            else:
                logger.info(f"No reports found for user {user_id}")
                return []

        except Exception as e:
            logger.error(f"Error retrieving user reports for {user_id}: {e}")
            return []

    async def update_status(self, report_id: str, status: str) -> None:
        """
        Update the status of a report.

        Args:
            report_id: UUID of the report
            status: New status (pending, processing, completed, error)

        Raises:
            ValueError: If update operation fails
        """
        valid_statuses = {"pending", "processing", "completed", "error"}
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        try:
            result = (
                self.db.table(self.reports_table)
                .update({
                    "status": status,
                    "updated_at": datetime.utcnow().isoformat(),
                })
                .eq("id", report_id)
                .execute()
            )

            if result.data:
                logger.info(f"Report status updated: {report_id} -> {status}")
            else:
                raise ValueError(f"Failed to update report status: {result.error}")

        except Exception as e:
            logger.error(f"Error updating report status for {report_id}: {e}")
            raise ValueError(f"Database error while updating report: {str(e)}")

    async def add_chat_message(
        self, report_id: str, role: str, content: str
    ) -> None:
        """
        Add a message to the chat history for a report.

        Args:
            report_id: UUID of the report
            role: Either "user" or "assistant"
            content: Message content

        Raises:
            ValueError: If operation fails
        """
        if role not in {"user", "assistant"}:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")

        try:
            # Get existing chat history
            chat_result = (
                self.db.table(self.chat_history_table)
                .select("*")
                .eq("report_id", report_id)
                .single()
                .execute()
            )

            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if chat_result.data:
                # Update existing chat history
                messages = chat_result.data.get("messages", [])
                messages.append(message)

                self.db.table(self.chat_history_table).update({
                    "messages": messages,
                    "message_count": len(messages),
                    "updated_at": datetime.utcnow().isoformat(),
                }).eq("report_id", report_id).execute()

                logger.info(f"Chat message added to {report_id}")
            else:
                # Create new chat history
                chat_history_id = str(uuid.uuid4())
                self.db.table(self.chat_history_table).insert({
                    "id": chat_history_id,
                    "report_id": report_id,
                    "messages": [message],
                    "message_count": 1,
                    "created_at": datetime.utcnow().isoformat(),
                }).execute()

                logger.info(f"Chat history created for {report_id}")

        except Exception as e:
            logger.error(f"Error adding chat message for {report_id}: {e}")
            raise ValueError(f"Failed to add chat message: {str(e)}")

    async def get_chat_history(self, report_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve chat history for a report.

        Args:
            report_id: UUID of the report

        Returns:
            list[dict]: List of chat messages
        """
        try:
            result = (
                self.db.table(self.chat_history_table)
                .select("messages")
                .eq("report_id", report_id)
                .single()
                .execute()
            )

            if result.data:
                messages = result.data.get("messages", [])
                logger.info(f"Retrieved {len(messages)} chat messages for {report_id}")
                return messages
            else:
                logger.info(f"No chat history found for {report_id}")
                return []

        except Exception as e:
            logger.error(f"Error retrieving chat history for {report_id}: {e}")
            return []

    async def delete_report(self, report_id: str) -> None:
        """
        Delete a report and its associated chat history.

        Args:
            report_id: UUID of the report

        Raises:
            ValueError: If delete operation fails
        """
        try:
            # Delete chat history first
            self.db.table(self.chat_history_table).delete().eq(
                "report_id", report_id
            ).execute()

            # Delete report
            result = (
                self.db.table(self.reports_table)
                .delete()
                .eq("id", report_id)
                .execute()
            )

            if result:
                logger.info(f"Report deleted: {report_id}")
            else:
                raise ValueError(f"Failed to delete report: {result.error}")

        except Exception as e:
            logger.error(f"Error deleting report {report_id}: {e}")
            raise ValueError(f"Database error while deleting report: {str(e)}")

    async def get_report_summary_stats(
        self, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for reports.

        Args:
            user_id: Optional user ID to get stats for specific user

        Returns:
            dict: Statistics including total count, average parameters, etc.
        """
        try:
            query = self.db.table(self.reports_table).select("id, created_at, status")

            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()
            reports = result.data or []

            completed = sum(1 for r in reports if r.get("status") == "completed")
            processing = sum(1 for r in reports if r.get("status") == "processing")
            errors = sum(1 for r in reports if r.get("status") == "error")

            stats = {
                "total_reports": len(reports),
                "completed": completed,
                "processing": processing,
                "error": errors,
                "user_id": user_id,
            }

            logger.info(f"Generated stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting report stats: {e}")
            return {"error": str(e)}
