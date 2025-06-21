"""
Data export service for exporting trip data to Excel/CSV formats.
"""

import io
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import base64

import pandas as pd
from azure.storage.blob import BlobServiceClient

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.core.telemetry import monitoring

settings = get_settings()
logger = get_logger(__name__)


class DataExportService:
    """Service for exporting trip data to various formats."""

    def __init__(self):
        self.blob_service_client = None
        self._setup_blob_client()

    def _setup_blob_client(self):
        """Setup Azure Blob Storage client."""
        if settings.AZURE_STORAGE_CONNECTION_STRING:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    settings.AZURE_STORAGE_CONNECTION_STRING
                )
                logger.info("Azure Blob Storage client initialized for exports")
            except Exception as e:
                logger.error(f"Failed to initialize blob storage client: {e}")

    async def export_trip_data_excel(
        self,
        trip_data: Dict[str, Any],
        trip_id: str,
        user_id: str,
        include_itinerary: bool = True,
        include_participants: bool = True,
        include_budget: bool = True,
    ) -> Dict[str, Any]:
        """Export comprehensive trip data to Excel format."""

        try:
            # Track the operation
            await monitoring.track_ai_operation("data_export_excel", 0)

            # Create Excel workbook with multiple sheets
            excel_data = {}

            # Trip Overview Sheet
            excel_data["Trip_Overview"] = self._prepare_trip_overview_data(trip_data)

            # Participants Sheet
            if include_participants and trip_data.get("participations"):
                excel_data["Participants"] = self._prepare_participants_data(
                    trip_data["participations"]
                )

            # Itinerary Sheet
            if include_itinerary and trip_data.get("itinerary_data"):
                itinerary_data = trip_data["itinerary_data"]
                if isinstance(itinerary_data, str):
                    itinerary_data = json.loads(itinerary_data)
                excel_data["Itinerary"] = self._prepare_itinerary_data(itinerary_data)

            # Budget Sheet
            if include_budget:
                excel_data["Budget"] = self._prepare_budget_data(trip_data)

            # Create Excel buffer
            excel_buffer = io.BytesIO()

            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                for sheet_name, data in excel_data.items():
                    if data:  # Only add non-empty sheets
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

            excel_buffer.seek(0)
            excel_bytes = excel_buffer.getvalue()

            # Upload to blob storage if available
            blob_url = None
            if self.blob_service_client:
                blob_url = await self._upload_to_blob_storage(
                    excel_bytes,
                    f"exports/{trip_id}/trip_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                )

            result = {
                "success": True,
                "format": "excel",
                "file_size": len(excel_bytes),
                "sheets": list(excel_data.keys()),
                "generated_at": datetime.now().isoformat(),
                "trip_id": trip_id,
                "user_id": user_id,
            }

            if blob_url:
                result["download_url"] = blob_url
            else:
                result["file_data"] = base64.b64encode(excel_bytes).decode("utf-8")

            logger.info(
                "Excel export completed",
                trip_id=trip_id,
                user_id=user_id,
                sheets=len(excel_data),
                size=len(excel_bytes),
            )

            return result

        except Exception as e:
            logger.error(f"Failed to export Excel data: {e}", trip_id=trip_id, user_id=user_id)
            raise

    async def export_trip_data_csv(
        self,
        trip_data: Dict[str, Any],
        trip_id: str,
        user_id: str,
        export_type: str = "itinerary",  # itinerary, participants, budget, all
    ) -> Dict[str, Any]:
        """Export trip data to CSV format."""

        try:
            await monitoring.track_ai_operation("data_export_csv", 0)

            csv_files = {}

            if export_type in ["itinerary", "all"]:
                if trip_data.get("itinerary_data"):
                    itinerary_data = trip_data["itinerary_data"]
                    if isinstance(itinerary_data, str):
                        itinerary_data = json.loads(itinerary_data)
                    csv_files["itinerary"] = self._create_itinerary_csv(itinerary_data)

            if export_type in ["participants", "all"]:
                if trip_data.get("participations"):
                    csv_files["participants"] = self._create_participants_csv(
                        trip_data["participations"]
                    )

            if export_type in ["budget", "all"]:
                csv_files["budget"] = self._create_budget_csv(trip_data)

            # If single export, return that file
            if len(csv_files) == 1:
                file_name, csv_content = next(iter(csv_files.items()))
                blob_url = None

                if self.blob_service_client:
                    blob_url = await self._upload_to_blob_storage(
                        csv_content.encode("utf-8"),
                        f"exports/{trip_id}/{file_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    )

                result = {
                    "success": True,
                    "format": "csv",
                    "file_size": len(csv_content.encode("utf-8")),
                    "export_type": export_type,
                    "generated_at": datetime.now().isoformat(),
                    "trip_id": trip_id,
                    "user_id": user_id,
                }

                if blob_url:
                    result["download_url"] = blob_url
                else:
                    result["file_data"] = base64.b64encode(csv_content.encode("utf-8")).decode(
                        "utf-8"
                    )

                return result

            # Multiple files - create a zip
            else:
                zip_buffer = io.BytesIO()
                import zipfile

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for file_name, csv_content in csv_files.items():
                        zip_file.writestr(f"{file_name}.csv", csv_content)

                zip_buffer.seek(0)
                zip_bytes = zip_buffer.getvalue()

                blob_url = None
                if self.blob_service_client:
                    blob_url = await self._upload_to_blob_storage(
                        zip_bytes,
                        f"exports/{trip_id}/trip_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    )

                result = {
                    "success": True,
                    "format": "csv_zip",
                    "file_size": len(zip_bytes),
                    "files": list(csv_files.keys()),
                    "generated_at": datetime.now().isoformat(),
                    "trip_id": trip_id,
                    "user_id": user_id,
                }

                if blob_url:
                    result["download_url"] = blob_url
                else:
                    result["file_data"] = base64.b64encode(zip_bytes).decode("utf-8")

                return result

        except Exception as e:
            logger.error(f"Failed to export CSV data: {e}", trip_id=trip_id, user_id=user_id)
            raise

    def _prepare_trip_overview_data(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare trip overview data for export."""
        overview = [
            {"Field": "Trip ID", "Value": trip_data.get("id", "")},
            {"Field": "Trip Name", "Value": trip_data.get("name", "")},
            {"Field": "Description", "Value": trip_data.get("description", "")},
            {"Field": "Destination", "Value": trip_data.get("destination", "")},
            {"Field": "Start Date", "Value": trip_data.get("start_date", "")},
            {"Field": "End Date", "Value": trip_data.get("end_date", "")},
            {"Field": "Status", "Value": trip_data.get("status", "")},
            {"Field": "Total Budget", "Value": trip_data.get("budget_total", 0)},
            {"Field": "Creator ID", "Value": trip_data.get("creator_id", "")},
            {"Field": "Family Count", "Value": trip_data.get("family_count", 0)},
            {"Field": "Confirmed Families", "Value": trip_data.get("confirmed_families", 0)},
            {"Field": "Has Itinerary", "Value": trip_data.get("has_itinerary", False)},
            {"Field": "Created At", "Value": trip_data.get("created_at", "")},
            {"Field": "Updated At", "Value": trip_data.get("updated_at", "")},
        ]
        return overview

    def _prepare_participants_data(
        self, participations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prepare participants data for export."""
        participants = []
        for participation in participations:
            participant = {
                "Participation ID": participation.get("id", ""),
                "Trip ID": participation.get("trip_id", ""),
                "Family ID": participation.get("family_id", ""),
                "User ID": participation.get("user_id", ""),
                "Status": participation.get("status", ""),
                "Budget Allocation": participation.get("budget_allocation", 0),
                "Notes": participation.get("notes", ""),
                "Joined At": participation.get("joined_at", ""),
                "Updated At": participation.get("updated_at", ""),
            }

            # Add preferences if available
            preferences = participation.get("preferences", {})
            if isinstance(preferences, dict):
                for key, value in preferences.items():
                    participant[f"Preference_{key}"] = value

            participants.append(participant)

        return participants

    def _prepare_itinerary_data(self, itinerary_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare itinerary data for export."""
        itinerary_rows = []

        # Add overview information
        overview = itinerary_data.get("overview", {})
        if overview:
            itinerary_rows.append(
                {
                    "Type": "Overview",
                    "Day": "N/A",
                    "Title": overview.get("title", ""),
                    "Description": overview.get("description", ""),
                    "Location": overview.get("destination", ""),
                    "Duration": "N/A",
                    "Cost": overview.get("total_budget", 0),
                    "Category": "Overview",
                }
            )

        # Add daily itinerary
        daily_itinerary = itinerary_data.get("daily_itinerary", [])
        for day_data in daily_itinerary:
            day_number = day_data.get("day", "Unknown")
            day_title = day_data.get("title", "")

            activities = day_data.get("activities", [])
            if not activities:
                # Add day header even if no activities
                itinerary_rows.append(
                    {
                        "Type": "Day",
                        "Day": day_number,
                        "Title": day_title,
                        "Description": day_data.get("description", ""),
                        "Location": day_data.get("location", ""),
                        "Duration": "Full Day",
                        "Cost": day_data.get("estimated_cost", 0),
                        "Category": "Day Header",
                    }
                )
            else:
                for activity in activities:
                    itinerary_rows.append(
                        {
                            "Type": "Activity",
                            "Day": day_number,
                            "Title": activity.get("name", ""),
                            "Description": activity.get("description", ""),
                            "Location": activity.get("location", ""),
                            "Duration": activity.get("duration", ""),
                            "Cost": activity.get("cost", 0),
                            "Category": activity.get("category", "General"),
                            "Start Time": activity.get("start_time", ""),
                            "End Time": activity.get("end_time", ""),
                        }
                    )

        return itinerary_rows

    def _prepare_budget_data(self, trip_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare budget data for export."""
        budget_rows = []

        # Trip level budget
        budget_rows.append(
            {
                "Category": "Trip Total",
                "Description": "Total trip budget",
                "Amount": trip_data.get("budget_total", 0),
                "Type": "Total",
                "Family": "All",
            }
        )

        # Family budget allocations
        participations = trip_data.get("participations", [])
        for participation in participations:
            if participation.get("budget_allocation"):
                budget_rows.append(
                    {
                        "Category": "Family Allocation",
                        "Description": f"Budget allocation for family {participation.get('family_id', '')}",
                        "Amount": participation.get("budget_allocation", 0),
                        "Type": "Allocation",
                        "Family": participation.get("family_id", ""),
                    }
                )

        # Extract budget breakdown from itinerary if available
        itinerary_data = trip_data.get("itinerary_data")
        if itinerary_data:
            if isinstance(itinerary_data, str):
                itinerary_data = json.loads(itinerary_data)

            budget_summary = itinerary_data.get("budget_summary", {})
            breakdown = budget_summary.get("breakdown", {})

            for category, amount in breakdown.items():
                budget_rows.append(
                    {
                        "Category": category.replace("_", " ").title(),
                        "Description": f"Estimated cost for {category}",
                        "Amount": amount,
                        "Type": "Estimate",
                        "Family": "All",
                    }
                )

        return budget_rows

    def _create_itinerary_csv(self, itinerary_data: Dict[str, Any]) -> str:
        """Create CSV content for itinerary data."""
        rows = self._prepare_itinerary_data(itinerary_data)

        output = io.StringIO()
        if rows:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return output.getvalue()

    def _create_participants_csv(self, participations: List[Dict[str, Any]]) -> str:
        """Create CSV content for participants data."""
        rows = self._prepare_participants_data(participations)

        output = io.StringIO()
        if rows:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return output.getvalue()

    def _create_budget_csv(self, trip_data: Dict[str, Any]) -> str:
        """Create CSV content for budget data."""
        rows = self._prepare_budget_data(trip_data)

        output = io.StringIO()
        if rows:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return output.getvalue()

    async def _upload_to_blob_storage(self, file_data: bytes, blob_name: str) -> Optional[str]:
        """Upload file to Azure Blob Storage."""
        if not self.blob_service_client:
            return None

        try:
            container_name = settings.AZURE_STORAGE_CONTAINER_NAME or "exports"

            # Create container if it doesn't exist
            try:
                self.blob_service_client.create_container(container_name)
            except Exception:
                # Container might already exist
                pass

            # Upload blob
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )

            blob_client.upload_blob(file_data, overwrite=True)

            # Return the blob URL
            return blob_client.url

        except Exception as e:
            logger.error(f"Failed to upload export to blob storage: {e}")
            return None

    async def export_activity_summary(
        self, itinerary_data: Dict[str, Any], trip_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Export activity summary for quick reference."""

        try:
            activities = []
            daily_itinerary = itinerary_data.get("daily_itinerary", [])

            for day_data in daily_itinerary:
                day_number = day_data.get("day", "Unknown")
                day_activities = day_data.get("activities", [])

                for activity in day_activities:
                    activities.append(
                        {
                            "Day": day_number,
                            "Activity": activity.get("name", ""),
                            "Location": activity.get("location", ""),
                            "Time": f"{activity.get('start_time', '')} - {activity.get('end_time', '')}",
                            "Duration": activity.get("duration", ""),
                            "Cost": activity.get("cost", 0),
                            "Category": activity.get("category", ""),
                            "Description": (
                                activity.get("description", "")[:100] + "..."
                                if len(activity.get("description", "")) > 100
                                else activity.get("description", "")
                            ),
                        }
                    )

            # Create CSV
            output = io.StringIO()
            if activities:
                fieldnames = activities[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(activities)

            csv_content = output.getvalue()

            # Upload to blob storage
            blob_url = None
            if self.blob_service_client:
                blob_url = await self._upload_to_blob_storage(
                    csv_content.encode("utf-8"),
                    f"exports/{trip_id}/activity_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                )

            result = {
                "success": True,
                "format": "csv",
                "export_type": "activity_summary",
                "activity_count": len(activities),
                "file_size": len(csv_content.encode("utf-8")),
                "generated_at": datetime.now().isoformat(),
                "trip_id": trip_id,
                "user_id": user_id,
            }

            if blob_url:
                result["download_url"] = blob_url
            else:
                result["file_data"] = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")

            logger.info(f"Activity summary exported", trip_id=trip_id, activities=len(activities))
            return result

        except Exception as e:
            logger.error(f"Failed to export activity summary: {e}", trip_id=trip_id)
            raise


# Global export service instance
export_service = DataExportService()
