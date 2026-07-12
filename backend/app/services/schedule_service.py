"""
IntelliHall — Schedule Service

Business logic for the maintenance schedule view and PDF export.
"""

from __future__ import annotations

import io
import logging
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import ComplaintAssignment
from app.models.complaint import Complaint
from app.models.enums import ComplaintCategory, ComplaintStatus, MaintenanceType
from app.schemas.schedule import ScheduleFilters, ScheduleItemRead

if TYPE_CHECKING:
    from app.models.user import User

logger = logging.getLogger(__name__)


class ScheduleService:
    """Service for schedule listing and PDF export."""

    @staticmethod
    async def list_schedule(
        session: AsyncSession,
        hall_id: str,
        filters: ScheduleFilters,
        current_user: "User",
    ) -> list[ScheduleItemRead]:
        """
        Return all scheduled/in-progress complaints for a hall with assignment info.
        Only accessible by the hall admin of that hall.
        """
        if current_user.hall_id != hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view the schedule for your own hall.",
            )

        # Join complaints with assignments
        stmt = (
            select(Complaint, ComplaintAssignment)
            .join(
                ComplaintAssignment,
                ComplaintAssignment.complaint_id == Complaint.id,
            )
            .where(
                Complaint.hall_id == hall_id,
                Complaint.status.in_([
                    ComplaintStatus.SCHEDULED,
                    ComplaintStatus.IN_PROGRESS,
                ]),
            )
        )

        # Apply filters
        if filters.scheduled_date is not None:
            stmt = stmt.where(
                ComplaintAssignment.scheduled_date == filters.scheduled_date
            )
        if filters.worker_name is not None:
            stmt = stmt.where(
                ComplaintAssignment.worker_name.ilike(f"%{filters.worker_name}%")
            )
        if filters.worker_type is not None:
            stmt = stmt.where(
                ComplaintAssignment.worker_type == filters.worker_type
            )
        if filters.category is not None:
            stmt = stmt.where(Complaint.category == filters.category)

        stmt = stmt.order_by(
            ComplaintAssignment.scheduled_date.asc(),
            Complaint.created_at.asc(),
        )

        result = await session.execute(stmt)
        rows = result.all()

        items: list[ScheduleItemRead] = []
        for complaint, assignment in rows:
            items.append(
                ScheduleItemRead(
                    complaint_id=complaint.id,
                    complaint_title=complaint.title,
                    room_number=complaint.room_number,
                    category=complaint.category,
                    status=complaint.status,
                    visit_date=assignment.scheduled_date,
                    scheduled_time=assignment.scheduled_time,
                    worker_name=assignment.worker_name,
                    worker_type=assignment.worker_type,
                    admin_remarks=assignment.admin_remarks,
                )
            )
        return items

    @staticmethod
    def export_pdf(
        schedule_items: list[ScheduleItemRead],
        hall_name: str,
        export_date: date,
    ) -> bytes:
        """
        Generate a PDF of the maintenance work schedule using reportlab.
        Returns raw PDF bytes.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                HRFlowable,
                Table,
                TableStyle,
            )
            from reportlab.lib import colors
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PDF generation library (reportlab) is not installed.",
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=16,
            alignment=1,  # center
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            alignment=1,
            textColor=colors.grey,
            spaceAfter=10,
        )
        heading_style = ParagraphStyle(
            "Heading",
            parent=styles["Heading3"],
            fontSize=11,
            spaceAfter=4,
            spaceBefore=8,
        )
        normal_style = styles["Normal"]
        normal_style.fontSize = 9

        story = []

        # Title
        story.append(Paragraph("INTELLIHALL", title_style))
        story.append(Paragraph("Maintenance Work Schedule", title_style))
        story.append(Paragraph(f"Hall: {hall_name}    Date: {export_date.strftime('%d %B %Y')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
        story.append(Spacer(1, 8))

        if not schedule_items:
            story.append(Paragraph("No scheduled maintenance work found.", normal_style))
        else:
            # Group by worker
            from itertools import groupby
            sorted_items = sorted(schedule_items, key=lambda x: (x.worker_name, x.visit_date))

            for worker_name, group in groupby(sorted_items, key=lambda x: x.worker_name):
                worker_items = list(group)
                worker_type = worker_items[0].worker_type.value.replace("_", " ").title()

                story.append(Paragraph(
                    f"Worker: {worker_name}    Type: {worker_type}",
                    heading_style,
                ))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))

                # Table for this worker's items
                table_data = [["Visit Date", "Time", "Room", "Category", "Complaint", "Remarks"]]
                for item in worker_items:
                    table_data.append([
                        item.visit_date.strftime("%d %b %Y"),
                        item.scheduled_time or "TBD",
                        item.room_number or "—",
                        item.category.value.replace("_", " ").title(),
                        item.complaint_title[:40] + ("…" if len(item.complaint_title) > 40 else ""),
                        (item.admin_remarks or "—")[:30],
                    ])

                col_widths = [25 * mm, 22 * mm, 18 * mm, 22 * mm, 55 * mm, 28 * mm]
                table = Table(table_data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(table)
                story.append(Spacer(1, 8))

        # Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Paragraph(
            f"Generated by IntelliHall on {datetime.now(timezone.utc).strftime('%d %B %Y %H:%M UTC')}",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.grey, alignment=1),
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()
