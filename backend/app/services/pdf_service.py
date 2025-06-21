"""
PDF service for generating trip documents and itineraries.
Creates formatted PDF documents for trip information, itineraries, and reports.
"""

import io
import logging
from datetime import datetime
from typing import Any, Dict, List

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.tableofcontents import TableOfContents
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("ReportLab not installed. PDF generation will not work.")

    # Mock classes for when reportlab is not available
    class SimpleDocTemplate:
        def __init__(self, *args, **kwargs):
            pass

        def build(self, *args, **kwargs):
            pass

    class Paragraph:
        def __init__(self, *args, **kwargs):
            pass

    class Spacer:
        def __init__(self, *args, **kwargs):
            pass

    letter = A4 = (612, 792)
    inch = 72

from app.models.family import Family
from app.models.itinerary import Itinerary, ItineraryActivity, ItineraryDay
from app.models.reservation import Reservation
from app.models.trip import TripDetail

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF documents."""

    def __init__(self):
        self.styles = (
            getSampleStyleSheet() if "getSampleStyleSheet" in globals() else {}
        )
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom PDF styles."""
        if not self.styles:
            return

        # Title style
        self.styles.add(
            ParagraphStyle(
                "CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue,
            )
        )

        # Header style
        self.styles.add(
            ParagraphStyle(
                "CustomHeader",
                parent=self.styles["Heading2"],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue,
            )
        )

        # Subheader style
        self.styles.add(
            ParagraphStyle(
                "CustomSubHeader",
                parent=self.styles["Heading3"],
                fontSize=14,
                spaceAfter=8,
                textColor=colors.blue,
            )
        )

        # Body text style
        self.styles.add(
            ParagraphStyle(
                "CustomBody",
                parent=self.styles["Normal"],
                fontSize=11,
                spaceAfter=6,
                leftIndent=20,
            )
        )

    def generate_trip_itinerary_pdf(
        self,
        trip: TripDetail,
        itinerary: Itinerary,
        itinerary_days: List[ItineraryDay],
        activities: Dict[str, List[ItineraryActivity]],
    ) -> bytes:
        """
        Generate a complete trip itinerary PDF.

        Args:
            trip: Trip details
            itinerary: Itinerary data
            itinerary_days: List of itinerary days
            activities: Dictionary mapping day IDs to activities

        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()

        try:
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            story = []

            # Title page
            story.extend(self._create_title_page(trip, itinerary))

            # Trip overview
            story.extend(self._create_trip_overview(trip))

            # Daily itinerary
            story.extend(self._create_daily_itinerary(
                itinerary_days, activities))

            # Important information
            story.extend(self._create_important_info(trip))

            doc.build(story)

            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error generating trip itinerary PDF: {e}")
            raise
        finally:
            buffer.close()

    def _create_title_page(self, trip: TripDetail, itinerary: Itinerary) -> List[Any]:
        """Create the title page elements."""
        elements = []

        # Title
        title = Paragraph(
            f"Trip Itinerary: {trip.name}",
            self.styles.get("CustomTitle", self.styles.get("Title")),
        )
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Destination
        destination = Paragraph(
            f"Destination: {trip.destination}",
            self.styles.get("CustomHeader", self.styles.get("Heading2")),
        )
        elements.append(destination)
        elements.append(Spacer(1, 15))

        # Dates
        dates = Paragraph(
            f"Dates: {trip.start_date.strftime('%B %d, %Y')} - {trip.end_date.strftime('%B %d, %Y')}",
            self.styles.get("CustomBody", self.styles.get("Normal")),
        )
        elements.append(dates)
        elements.append(Spacer(1, 10))

        # Duration
        duration = (trip.end_date - trip.start_date).days + 1
        duration_text = Paragraph(
            f"Duration: {duration} days",
            self.styles.get("CustomBody", self.styles.get("Normal")),
        )
        elements.append(duration_text)
        elements.append(Spacer(1, 30))

        # Description
        if trip.description:
            desc_title = Paragraph(
                "Trip Description",
                self.styles.get("CustomSubHeader",
                                self.styles.get("Heading3")),
            )
            elements.append(desc_title)
            description = Paragraph(
                trip.description,
                self.styles.get("CustomBody", self.styles.get("Normal")),
            )
            elements.append(description)
            elements.append(Spacer(1, 20))

        # Generated info
        generated_text = Paragraph(
            f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.styles.get("Normal"),
        )
        elements.append(generated_text)

        return elements

    def _create_trip_overview(self, trip: TripDetail) -> List[Any]:
        """Create trip overview section."""
        elements = []

        # Section header
        header = Paragraph(
            "Trip Overview",
            self.styles.get("CustomHeader", self.styles.get("Heading2")),
        )
        elements.append(header)
        elements.append(Spacer(1, 12))

        # Trip details table
        trip_data = [
            ["Trip Name:", trip.name],
            ["Destination:", trip.destination],
            ["Start Date:", trip.start_date.strftime("%B %d, %Y")],
            ["End Date:", trip.end_date.strftime("%B %d, %Y")],
            ["Status:", trip.status.value.title()],
        ]

        if trip.budget_total:
            trip_data.append(["Budget:", f"${trip.budget_total:,.2f}"])

        trip_table = Table(trip_data, colWidths=[2 * inch, 4 * inch])
        trip_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        elements.append(trip_table)
        elements.append(Spacer(1, 20))

        # Participants
        if hasattr(trip, "participations") and trip.participations:
            participants_header = Paragraph(
                "Participants",
                self.styles.get("CustomSubHeader",
                                self.styles.get("Heading3")),
            )
            elements.append(participants_header)

            for participation in trip.participations:
                participant_text = (
                    f"• {participation.user.name} ({participation.family.name})"
                )
                if participation.status:
                    participant_text += f" - {participation.status.value.title()}"

                participant = Paragraph(
                    participant_text,
                    self.styles.get("CustomBody", self.styles.get("Normal")),
                )
                elements.append(participant)

            elements.append(Spacer(1, 20))

        return elements

    def _create_daily_itinerary(
        self,
        itinerary_days: List[ItineraryDay],
        activities: Dict[str, List[ItineraryActivity]],
    ) -> List[Any]:
        """Create daily itinerary section."""
        elements = []

        # Section header
        header = Paragraph(
            "Daily Itinerary",
            self.styles.get("CustomHeader", self.styles.get("Heading2")),
        )
        elements.append(header)
        elements.append(Spacer(1, 12))

        for day in sorted(itinerary_days, key=lambda d: d.day_number):
            # Day header
            day_header = Paragraph(
                f"Day {day.day_number}: {day.date.strftime('%A, %B %d, %Y')}",
                self.styles.get("CustomSubHeader",
                                self.styles.get("Heading3")),
            )
            elements.append(day_header)

            if day.theme:
                theme = Paragraph(
                    f"Theme: {day.theme}",
                    self.styles.get("CustomBody", self.styles.get("Normal")),
                )
                elements.append(theme)

            elements.append(Spacer(1, 8))

            # Day activities
            day_activities = activities.get(str(day.id), [])
            if day_activities:
                for activity in sorted(
                    day_activities, key=lambda a: a.start_time or datetime.min.time()
                ):
                    activity_elements = self._create_activity_entry(activity)
                    elements.extend(activity_elements)
            else:
                no_activities = Paragraph(
                    "No activities scheduled for this day.",
                    self.styles.get("CustomBody", self.styles.get("Normal")),
                )
                elements.append(no_activities)

            elements.append(Spacer(1, 15))

        return elements

    def _create_activity_entry(self, activity: ItineraryActivity) -> List[Any]:
        """Create activity entry elements."""
        elements = []

        # Activity time and name
        time_str = ""
        if activity.start_time:
            time_str = activity.start_time.strftime("%I:%M %p")
            if activity.end_time:
                time_str += f" - {activity.end_time.strftime('%I:%M %p')}"

        activity_title = f"{time_str} - {activity.name}" if time_str else activity.name
        title = Paragraph(
            activity_title, self.styles.get(
                "CustomBody", self.styles.get("Normal"))
        )
        elements.append(title)

        # Activity details
        details = []
        if activity.location:
            details.append(f"Location: {activity.location}")
        if activity.description:
            details.append(f"Description: {activity.description}")
        if activity.estimated_cost:
            details.append(f"Estimated Cost: ${activity.estimated_cost}")
        if activity.duration_minutes:
            hours = activity.duration_minutes // 60
            minutes = activity.duration_minutes % 60
            duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            details.append(f"Duration: {duration_str}")

        for detail in details:
            detail_para = Paragraph(
                f"  {detail}", self.styles.get(
                    "CustomBody", self.styles.get("Normal"))
            )
            elements.append(detail_para)

        elements.append(Spacer(1, 8))
        return elements

    def _create_important_info(self, trip: TripDetail) -> List[Any]:
        """Create important information section."""
        elements = []

        # Section header
        header = Paragraph(
            "Important Information",
            self.styles.get("CustomHeader", self.styles.get("Heading2")),
        )
        elements.append(header)
        elements.append(Spacer(1, 12))

        # Emergency contacts
        emergency_header = Paragraph(
            "Emergency Contacts",
            self.styles.get("CustomSubHeader", self.styles.get("Heading3")),
        )
        elements.append(emergency_header)

        # Standard emergency numbers
        emergency_info = [
            "• Emergency Services: 911",
            "• Trip Creator: Contact through app",
            "• Travel Insurance: Check your policy documents",
        ]

        for info in emergency_info:
            info_para = Paragraph(
                info, self.styles.get("CustomBody", self.styles.get("Normal"))
            )
            elements.append(info_para)

        elements.append(Spacer(1, 15))

        # Travel tips
        tips_header = Paragraph(
            "Travel Tips",
            self.styles.get("CustomSubHeader", self.styles.get("Heading3")),
        )
        elements.append(tips_header)

        tips = [
            "• Keep copies of important documents",
            "• Check weather forecasts daily",
            "• Stay hydrated and take breaks",
            "• Respect local customs and regulations",
            "• Keep emergency cash and cards separate",
            "• Download offline maps for your destination",
        ]

        for tip in tips:
            tip_para = Paragraph(
                tip, self.styles.get("CustomBody", self.styles.get("Normal"))
            )
            elements.append(tip_para)

        return elements

    def generate_trip_summary_pdf(
        self, trip: TripDetail, reservations: List[Reservation] = None
    ) -> bytes:
        """
        Generate a trip summary PDF with key information.

        Args:
            trip: Trip details
            reservations: Optional list of reservations

        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()

        try:
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []

            # Title
            title = Paragraph(
                f"Trip Summary: {trip.name}",
                self.styles.get("CustomTitle", self.styles.get("Title")),
            )
            story.append(title)
            story.append(Spacer(1, 20))

            # Trip overview
            story.extend(self._create_trip_overview(trip))

            # Reservations summary
            if reservations:
                story.extend(self._create_reservations_summary(reservations))

            doc.build(story)

            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error generating trip summary PDF: {e}")
            raise
        finally:
            buffer.close()

    def _create_reservations_summary(
        self, reservations: List[Reservation]
    ) -> List[Any]:
        """Create reservations summary section."""
        elements = []

        # Section header
        header = Paragraph(
            "Reservations", self.styles.get(
                "CustomHeader", self.styles.get("Heading2"))
        )
        elements.append(header)
        elements.append(Spacer(1, 12))

        # Group reservations by type
        grouped_reservations = {}
        for reservation in reservations:
            res_type = reservation.reservation_type.value
            if res_type not in grouped_reservations:
                grouped_reservations[res_type] = []
            grouped_reservations[res_type].append(reservation)

        for res_type, res_list in grouped_reservations.items():
            type_header = Paragraph(
                res_type.title(),
                self.styles.get("CustomSubHeader",
                                self.styles.get("Heading3")),
            )
            elements.append(type_header)

            for reservation in res_list:
                res_elements = self._create_reservation_entry(reservation)
                elements.extend(res_elements)

            elements.append(Spacer(1, 10))

        return elements

    def _create_reservation_entry(self, reservation: Reservation) -> List[Any]:
        """Create reservation entry elements."""
        elements = []

        # Reservation name
        name = Paragraph(
            f"• {reservation.name}",
            self.styles.get("CustomBody", self.styles.get("Normal")),
        )
        elements.append(name)

        # Details
        details = []
        if reservation.provider:
            details.append(f"Provider: {reservation.provider}")
        if reservation.confirmation_number:
            details.append(f"Confirmation: {reservation.confirmation_number}")
        if reservation.check_in_date:
            details.append(
                f"Check-in: {reservation.check_in_date.strftime('%B %d, %Y')}"
            )
        if reservation.check_out_date:
            details.append(
                f"Check-out: {reservation.check_out_date.strftime('%B %d, %Y')}"
            )
        if reservation.total_cost:
            details.append(f"Cost: ${reservation.total_cost}")
        if reservation.status:
            details.append(f"Status: {reservation.status.value.title()}")

        for detail in details:
            detail_para = Paragraph(
                f"    {detail}",
                self.styles.get("CustomBody", self.styles.get("Normal")),
            )
            elements.append(detail_para)

        elements.append(Spacer(1, 5))
        return elements

    def generate_family_roster_pdf(self, families: List[Family]) -> bytes:
        """
        Generate a family roster PDF.

        Args:
            families: List of families with members

        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()

        try:
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []

            # Title
            title = Paragraph(
                "Family Roster",
                self.styles.get("CustomTitle", self.styles.get("Title")),
            )
            story.append(title)
            story.append(Spacer(1, 20))

            for family in families:
                # Family name
                family_header = Paragraph(
                    family.name,
                    self.styles.get(
                        "CustomHeader", self.styles.get("Heading2")),
                )
                story.append(family_header)
                story.append(Spacer(1, 8))

                # Family members
                if hasattr(family, "members") and family.members:
                    for member in family.members:
                        member_info = f"• {member.name}"
                        if member.age:
                            member_info += f" (Age: {member.age})"
                        if member.role:
                            member_info += f" - {member.role.value.title()}"

                        member_para = Paragraph(
                            member_info,
                            self.styles.get(
                                "CustomBody", self.styles.get("Normal")),
                        )
                        story.append(member_para)

                story.append(Spacer(1, 15))

            doc.build(story)

            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error generating family roster PDF: {e}")
            raise
        finally:
            buffer.close()


# Global service instance
pdf_service = PDFService()
