"""
Report Generator Utility
Extracts agent data from conversations and generates PDF/CSV reports

Enterprise Report Styling Specification v1.0
- A4 portrait layout with professional pharmaceutical styling
- ReportLab-based PDF generation with custom styling
- Consistent branding and formatting across all reports
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging
from io import BytesIO

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, Image, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# Enterprise Report Design System Constants
AVALON_PRIMARY = colors.HexColor("#0EA5E9")  # Avalon cyan
AVALON_SECONDARY = colors.HexColor("#1E293B")  # Slate-800
AVALON_TEXT = colors.HexColor("#111827")  # Slate-900
AVALON_SECTION_BG = colors.HexColor("#F1F5F9")  # Slate-100
AVALON_BORDER = colors.HexColor("#CBD5E1")  # Slate-300
AVALON_TABLE_HEADER = colors.HexColor("#E2E8F0")  # Slate-200
AVALON_FOOTER_TEXT = colors.HexColor("#6B7280")  # Gray-500

# Layout constants (A4 portrait)
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_TOP = 45
MARGIN_BOTTOM = 45
MARGIN_LEFT = 40
MARGIN_RIGHT = 40


def extract_agent_data(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract multi-agent research data from conversation messages.
    Looks for the last assistant message with metadata containing worker results.
    
    Returns:
        Dictionary with extracted data including:
        - executive_summary
        - sections (per-agent summaries)
        - data_tables (if any)
        - has_table boolean
    """
    # Find the last assistant message with metadata
    last_ai_message = None
    for msg in reversed(messages):
        if msg.get("role") == "assistant" and msg.get("metadata"):
            metadata = msg.get("metadata", {})
            if "workers" in metadata or "content" in metadata:
                last_ai_message = msg
                break
    
    if not last_ai_message:
        logger.warning("No AI message with worker data found")
        return {
            "executive_summary": [],
            "sections": [],
            "data_tables": [],
            "has_table": False,
            "full_text": "No research data available."
        }
    
    metadata = last_ai_message.get("metadata", {})
    workers = metadata.get("workers", {})
    content_text = last_ai_message.get("content", "")
    
    # Extract sections from workers
    sections = []
    data_tables = []
    
    # Define agent display names
    agent_names = {
        "market": "Market Analysis",
        "clinical": "Clinical Trials",
        "patents": "Patent Landscape",
        "exim": "Import/Export Intelligence",
        "internal_docs": "Internal Documents",
        "web": "Web Intelligence",
        "safety": "Safety & PK/PD",
        "expert_network": "Expert Network"
    }
    
    for agent_key, agent_data in workers.items():
        if not isinstance(agent_data, dict):
            continue
        
        agent_name = agent_names.get(agent_key, agent_key.replace("_", " ").title())
        
        # Extract summary
        summary = agent_data.get("summary", "")
        full_text = agent_data.get("full_text", "")
        
        # Extract key findings (look for bullet points or lists)
        key_findings = []
        insights = []
        
        # Try to extract structured data
        if "key_findings" in agent_data:
            findings = agent_data["key_findings"]
            if isinstance(findings, list):
                key_findings = findings
            elif isinstance(findings, str):
                key_findings = [findings]
        elif "findings" in agent_data:
            findings = agent_data["findings"]
            if isinstance(findings, list):
                key_findings = findings
        elif summary:
            # Parse summary for bullet points
            lines = summary.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                    key_findings.append(line.lstrip("-•* "))
        
        # Extract insights
        if "insights" in agent_data:
            insights_data = agent_data["insights"]
            if isinstance(insights_data, list):
                insights = insights_data
            elif isinstance(insights_data, str):
                insights = [insights_data]
        elif "key_insights" in agent_data:
            insights_data = agent_data["key_insights"]
            if isinstance(insights_data, list):
                insights = insights_data
        
        # Look for data tables (agent-specific)
        agent_tables = []
        if "data_tables" in agent_data:
            tables = agent_data["data_tables"]
            if isinstance(tables, list) and tables:
                agent_tables.extend(tables)
                data_tables.extend(tables)
        elif "table" in agent_data:
            agent_tables.append(agent_data["table"])
            data_tables.append(agent_data["table"])
        elif "tables" in agent_data:
            tables = agent_data["tables"]
            if isinstance(tables, list) and tables:
                agent_tables.extend(tables)
                data_tables.extend(tables)
        
        # Extract citations/provenance
        citations = agent_data.get("sources", [])
        if not citations:
            citations = agent_data.get("citations", [])
        
        provenance = agent_data.get("provenance", [])
        if not provenance:
            provenance = agent_data.get("metadata", [])
        
        section = {
            "agent": agent_name,
            "summary": summary or full_text[:500] if full_text else "No summary available",
            "key_findings": key_findings,
            "insights": insights,
            "citations": citations,
            "provenance": provenance,
            "tables": agent_tables  # Include agent-specific tables
        }
        
        sections.append(section)
    
    # Extract executive summary if available
    executive_summary = []
    if "executive_summary" in metadata:
        exec_sum = metadata["executive_summary"]
        if isinstance(exec_sum, list):
            executive_summary = exec_sum
        elif isinstance(exec_sum, str):
            executive_summary = [exec_sum]
    
    return {
        "executive_summary": executive_summary,
        "sections": sections,
        "data_tables": data_tables,
        "has_table": len(data_tables) > 0,
        "full_text": content_text
    }


class AvalonReportBuilder:
    """
    Enterprise-grade PDF report builder for Avalon.
    Implements the full Enterprise Report Styling Specification v1.0.
    """
    
    def __init__(self, title: str, conversation_id: str, report_id: str):
        self.title = title
        self.conversation_id = conversation_id
        self.report_id = report_id
        self.timestamp = datetime.utcnow().strftime("%B %d, %Y")
        self.story = []
        self.styles = self._create_styles()
        
    def _create_styles(self):
        """Create custom paragraph styles following Enterprise spec"""
        styles = getSampleStyleSheet()
        
        # H1 - Report Title
        styles.add(ParagraphStyle(
            name='AvalonH1',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=AVALON_TEXT,
            spaceAfter=12,
            spaceBefore=0,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        # H2 - Section Headers
        styles.add(ParagraphStyle(
            name='AvalonH2',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=AVALON_TEXT,
            spaceAfter=10,
            spaceBefore=14,
            fontName='Helvetica-Bold',
            leftIndent=12,
            borderWidth=0,
            borderColor=AVALON_PRIMARY,
            borderPadding=12,
            backColor=AVALON_SECTION_BG,
            borderRadius=2
        ))
        
        # H3 - Subsection Headers
        styles.add(ParagraphStyle(
            name='AvalonH3',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=AVALON_SECONDARY,
            spaceAfter=6,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Body Text
        styles.add(ParagraphStyle(
            name='AvalonBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=AVALON_TEXT,
            spaceAfter=8,
            spaceBefore=0,
            fontName='Helvetica',
            alignment=TA_JUSTIFY,
            leading=15
        ))
        
        # Bullet Points
        styles.add(ParagraphStyle(
            name='AvalonBullet',
            parent=styles['Normal'],
            fontSize=10.5,
            textColor=AVALON_TEXT,
            spaceAfter=4,
            spaceBefore=0,
            fontName='Helvetica',
            leftIndent=20,
            bulletIndent=8,
            leading=14
        ))
        
        # Cover Page Subtitle
        styles.add(ParagraphStyle(
            name='AvalonSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=AVALON_SECONDARY,
            spaceAfter=6,
            fontName='Helvetica',
            alignment=TA_CENTER
        ))
        
        # Footer Text
        styles.add(ParagraphStyle(
            name='AvalonFooter',
            parent=styles['Normal'],
            fontSize=9,
            textColor=AVALON_FOOTER_TEXT,
            fontName='Helvetica',
            alignment=TA_RIGHT
        ))
        
        # Metadata Text
        styles.add(ParagraphStyle(
            name='AvalonMeta',
            parent=styles['Normal'],
            fontSize=10,
            textColor=AVALON_SECONDARY,
            spaceAfter=4,
            fontName='Helvetica'
        ))
        
        # Cover Watermark
        styles.add(ParagraphStyle(
            name='AvalonWatermark',
            parent=styles['Normal'],
            fontSize=10,
            textColor=AVALON_FOOTER_TEXT,
            fontName='Helvetica-Oblique',
            alignment=TA_CENTER
        ))
        
        return styles
    
    def add_cover_page(self, agent_summary: List[str]):
        """Generate professional cover page (Page 1)"""
        # Title
        self.story.append(Spacer(1, 80))
        self.story.append(Paragraph("AVALON", self.styles['AvalonH1']))
        self.story.append(Spacer(1, 10))
        
        # Report Title
        title_para = Paragraph(self.title, self.styles['AvalonH1'])
        self.story.append(title_para)
        self.story.append(Spacer(1, 20))
        
        # Subtitle
        subtitle = Paragraph(
            "AI-Generated Pharmaceutical Research Report",
            self.styles['AvalonSubtitle']
        )
        self.story.append(subtitle)
        self.story.append(Spacer(1, 40))
        
        # Metadata section
        metadata_lines = [
            f"<b>Report Generated:</b> {self.timestamp}",
            f"<b>Report ID:</b> {self.report_id}",
            f"<b>Conversation ID:</b> {self.conversation_id[:16]}...",
            ""
        ]
        
        for line in metadata_lines:
            self.story.append(Paragraph(line, self.styles['AvalonMeta']))
        
        self.story.append(Spacer(1, 30))
        
        # Agents Used section
        self.story.append(Paragraph(
            "<b>Research Agents Deployed:</b>",
            self.styles['AvalonH3']
        ))
        self.story.append(Spacer(1, 8))
        
        agent_list = [
            "• Market Intelligence Agent",
            "• Clinical Trials Analysis Agent",
            "• Patent Landscape Agent",
            "• Import/Export Intelligence Agent",
            "• Web Intelligence Agent",
            "• Internal Documents Agent",
            "• Safety & PK/PD Agent",
            "• Expert Network Agent"
        ]
        
        for agent in agent_list:
            if any(a.lower() in agent.lower() for a in agent_summary):
                self.story.append(Paragraph(agent, self.styles['AvalonBullet']))
        
        # Footer watermark
        self.story.append(Spacer(1, 80))
        watermark = Paragraph(
            "Confidential Research — Not For Distribution",
            self.styles['AvalonWatermark']
        )
        self.story.append(watermark)
        
        # Page break
        self.story.append(PageBreak())
    
    def add_executive_summary(self, executive_summary: List[str]):
        """Generate Executive Summary (Page 2)"""
        # Title
        self.story.append(Paragraph("Executive Summary", self.styles['AvalonH1']))
        self.story.append(Spacer(1, 14))
        
        # Summary bullets
        if executive_summary and len(executive_summary) > 0:
            for item in executive_summary:
                bullet_text = f"• {item}"
                self.story.append(Paragraph(bullet_text, self.styles['AvalonBullet']))
                self.story.append(Spacer(1, 4))
        else:
            placeholder = (
                "This report synthesizes findings from Avalon's multi-agent research pipeline. "
                "Each section below presents insights from specialized research agents analyzing "
                "pharmaceutical data, clinical trials, market intelligence, and regulatory information."
            )
            self.story.append(Paragraph(placeholder, self.styles['AvalonBody']))
        
        self.story.append(Spacer(1, 20))
        
        # Attribution statement
        attribution = (
            "<i>This report is programmatically generated using Avalon's "
            "Multi-Agent Research Pipeline.</i>"
        )
        self.story.append(Paragraph(attribution, self.styles['AvalonMeta']))
        
        # Page break
        self.story.append(PageBreak())
    
    def add_agent_section(
        self,
        section_number: int,
        agent_name: str,
        summary: str,
        key_findings: List[str],
        insights: List[str],
        citations: List[Any],
        provenance: List[Any],
        tables: List[Any] = None
    ):
        """
        Add a single agent section following strict formatting rules.
        
        Section Order:
        1. Agent Title (H2 with styled block)
        2. Summary of Findings (H3)
        3. Key Insights (H3)
        4. Tables (H3) - if available
        5. Citations (H3)
        6. Provenance Notes (H3)
        """
        
        # 1. SECTION HEADER with background and border
        section_title = f"SECTION {section_number} — {agent_name}"
        
        # Create a table for the colored background header
        header_data = [[Paragraph(section_title, self.styles['AvalonH2'])]]
        header_table = Table(header_data, colWidths=[PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), AVALON_SECTION_BG),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, -1), 4, AVALON_PRIMARY),
        ]))
        
        self.story.append(header_table)
        self.story.append(Spacer(1, 12))
        
        # 2. SUMMARY OF FINDINGS
        self.story.append(Paragraph("Summary of Findings", self.styles['AvalonH3']))
        self.story.append(Spacer(1, 6))
        
        if summary:
            # Split long summaries into paragraphs
            summary_paras = summary.split('\n\n') if '\n\n' in summary else [summary]
            for para in summary_paras[:3]:  # Max 3 paragraphs
                if para.strip():
                    self.story.append(Paragraph(para.strip(), self.styles['AvalonBody']))
                    self.story.append(Spacer(1, 6))
        else:
            self.story.append(Paragraph(
                "No summary available for this agent.",
                self.styles['AvalonBody']
            ))
        
        self.story.append(Spacer(1, 10))
        
        # 3. KEY INSIGHTS
        self.story.append(Paragraph("Key Insights", self.styles['AvalonH3']))
        self.story.append(Spacer(1, 6))
        
        if key_findings and len(key_findings) > 0:
            for finding in key_findings:
                bullet = f"• {finding}"
                self.story.append(Paragraph(bullet, self.styles['AvalonBullet']))
                self.story.append(Spacer(1, 3))
        elif insights and len(insights) > 0:
            for insight in insights:
                bullet = f"• {insight}"
                self.story.append(Paragraph(bullet, self.styles['AvalonBullet']))
                self.story.append(Spacer(1, 3))
        else:
            self.story.append(Paragraph(
                "No key insights extracted.",
                self.styles['AvalonBody']
            ))
        
        self.story.append(Spacer(1, 10))
        
        # 4. TABLES (if available)
        self.story.append(Paragraph("Data Tables", self.styles['AvalonH3']))
        self.story.append(Spacer(1, 6))
        
        if tables and len(tables) > 0:
            # Render first table only
            table = tables[0]
            self._add_data_table(table)
        else:
            no_table = Paragraph(
                "<i>This agent produced no tabular data.</i>",
                self.styles['AvalonMeta']
            )
            self.story.append(no_table)
        
        self.story.append(Spacer(1, 10))
        
        # 5. CITATIONS
        self.story.append(Paragraph("Citations", self.styles['AvalonH3']))
        self.story.append(Spacer(1, 6))
        
        if citations and len(citations) > 0:
            citation_text = ", ".join(str(c) for c in citations[:8])  # Max 8 citations
            self.story.append(Paragraph(citation_text, self.styles['AvalonMeta']))
        else:
            self.story.append(Paragraph("No citations available.", self.styles['AvalonMeta']))
        
        self.story.append(Spacer(1, 10))
        
        # 6. PROVENANCE NOTES
        self.story.append(Paragraph("Provenance Notes", self.styles['AvalonH3']))
        self.story.append(Spacer(1, 6))
        
        if provenance and len(provenance) > 0:
            prov_text = ", ".join(str(p) for p in provenance[:5])
            self.story.append(Paragraph(prov_text, self.styles['AvalonMeta']))
        else:
            self.story.append(Paragraph(
                "Provenance data not recorded.",
                self.styles['AvalonMeta']
            ))
        
        # Section spacing
        self.story.append(Spacer(1, 18))
    
    def _add_data_table(self, table_data: Any):
        """Render a data table with enterprise styling"""
        try:
            headers = []
            rows = []
            
            # Parse table format
            if isinstance(table_data, dict):
                headers = table_data.get("headers", [])
                rows = table_data.get("rows", [])
            elif isinstance(table_data, list) and len(table_data) > 0:
                if isinstance(table_data[0], dict):
                    headers = list(table_data[0].keys())
                    rows = [[row.get(h, "") for h in headers] for row in table_data]
            
            if not headers or not rows:
                return
            
            # Build table data with wrapped text
            table_content = [[Paragraph(str(h), self.styles['AvalonMeta']) for h in headers]]
            for row in rows[:10]:  # Max 10 rows
                table_content.append([Paragraph(str(cell), self.styles['AvalonMeta']) for cell in row])
            
            # Calculate column widths
            num_cols = len(headers)
            col_width = (PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT) / num_cols
            
            # Create table
            data_table = Table(table_content, colWidths=[col_width] * num_cols)
            data_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), AVALON_TABLE_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), AVALON_TEXT),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Body styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), AVALON_TEXT),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 0.5, AVALON_BORDER),
                ('LINEBELOW', (0, 0), (-1, 0), 1, AVALON_BORDER),
                
                # Padding
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                
                # Alignment
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            self.story.append(data_table)
            self.story.append(Spacer(1, 8))
            
        except Exception as e:
            logger.error(f"Error rendering table: {e}")
            self.story.append(Paragraph(
                f"<i>Table rendering error: {str(e)}</i>",
                self.styles['AvalonMeta']
            ))
    

    
    def _add_page_footer(self, canvas_obj, doc):
        """Add footer to each page"""
        canvas_obj.saveState()
        
        # Footer text
        footer_text = "Generated by Avalon — Confidential Clinical Research"
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(AVALON_FOOTER_TEXT)
        
        # Right-aligned footer
        canvas_obj.drawRightString(
            PAGE_WIDTH - MARGIN_RIGHT,
            MARGIN_BOTTOM - 20,
            footer_text
        )
        
        # Page number (left side)
        page_num = f"Page {doc.page}"
        canvas_obj.drawString(
            MARGIN_LEFT,
            MARGIN_BOTTOM - 20,
            page_num
        )
        
        # Copyright notice (center)
        copyright_text = "© Avalon — AI-Driven Pharmaceutical Research Infrastructure"
        text_width = canvas_obj.stringWidth(copyright_text, 'Helvetica', 8)
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.drawString(
            (PAGE_WIDTH - text_width) / 2,
            MARGIN_BOTTOM - 30,
            copyright_text
        )
        
        canvas_obj.restoreState()


def generate_pdf_content(
    report_data: Dict[str, Any],
    title: str,
    conversation_id: str,
    report_id: str
) -> bytes:
    """
    Generate enterprise-grade PDF report using ReportLab.
    
    Returns:
        PDF file as bytes
    """
    # Create report builder
    builder = AvalonReportBuilder(title, conversation_id, report_id)
    
    # Extract agent names for cover page
    agent_names = [s.get("agent", "") for s in report_data.get("sections", [])]
    
    # Build report structure
    builder.add_cover_page(agent_names)
    builder.add_executive_summary(report_data.get("executive_summary", []))
    
    # Add each agent section
    sections = report_data.get("sections", [])
    for idx, section in enumerate(sections, start=1):
        # Get tables for this agent if available
        agent_tables = []
        if "tables" in section:
            agent_tables = section["tables"]
        
        builder.add_agent_section(
            section_number=idx,
            agent_name=section.get("agent", "Unknown Agent"),
            summary=section.get("summary", ""),
            key_findings=section.get("key_findings", []),
            insights=section.get("insights", []),
            citations=section.get("citations", []),
            provenance=section.get("provenance", []),
            tables=agent_tables
        )
    
    # Generate PDF to BytesIO
    buffer = BytesIO()
    
    try:
        # Use BytesIO directly with ReportLab
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=MARGIN_RIGHT,
            leftMargin=MARGIN_LEFT,
            topMargin=MARGIN_TOP,
            bottomMargin=MARGIN_BOTTOM,
            title=title,
            author="Avalon Pharmaceutical Research Platform"
        )
        
        doc.build(
            builder.story,
            onFirstPage=builder._add_page_footer,
            onLaterPages=builder._add_page_footer
        )
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        # Return empty PDF on error
        return b""


def generate_csv_content(report_data: Dict[str, Any]) -> str:
    """
    Generate CSV content (table only, or "No table available").
    
    Returns:
        CSV string with proper line breaks
    """
    data_tables = report_data.get("data_tables", [])
    
    if not data_tables:
        # No table available
        return "Message\nNo table available for this report."
    
    # Use the first table found
    first_table = data_tables[0]
    
    # Handle different table formats
    if isinstance(first_table, dict):
        # Check for headers and rows
        headers = first_table.get("headers", [])
        rows = first_table.get("rows", [])
        
        if headers and rows:
            # Build CSV with proper escaping
            csv_lines = []
            
            # Add headers
            header_line = ",".join(_escape_csv_cell(str(h)) for h in headers)
            csv_lines.append(header_line)
            
            # Add rows
            for row in rows:
                row_line = ",".join(_escape_csv_cell(str(cell)) for cell in row)
                csv_lines.append(row_line)
            
            return "\n".join(csv_lines)
        
        # Check for data as dict
        if "data" in first_table:
            data = first_table["data"]
            if isinstance(data, list) and data:
                # Assume list of dicts
                if isinstance(data[0], dict):
                    headers = list(data[0].keys())
                    csv_lines = [",".join(_escape_csv_cell(str(h)) for h in headers)]
                    
                    for row in data:
                        row_line = ",".join(_escape_csv_cell(str(row.get(h, ""))) for h in headers)
                        csv_lines.append(row_line)
                    
                    return "\n".join(csv_lines)
    
    elif isinstance(first_table, str):
        # Already a CSV string
        return first_table
    
    # Fallback
    return "Message\nTable data format not recognized."


def _escape_csv_cell(cell: str) -> str:
    """Escape CSV cell content (quotes, commas, newlines)"""
    cell = str(cell)
    
    # If cell contains comma, quote, or newline, wrap in quotes
    if ',' in cell or '"' in cell or '\n' in cell:
        # Escape quotes by doubling them
        cell = cell.replace('"', '""')
        return f'"{cell}"'
    
    return cell


async def save_report_files(
    report_id: str,
    pdf_content: bytes,
    csv_content: str,
    uploads_dir: str = "uploads/reports"
) -> Tuple[str, str, int, int]:
    """
    Save PDF (binary) and CSV files to disk.
    
    Args:
        report_id: Unique report identifier
        pdf_content: PDF file as bytes (from ReportLab)
        csv_content: CSV file as string
        uploads_dir: Directory to save files
    
    Returns:
        Tuple of (pdf_path, csv_path, pdf_size, csv_size)
    """
    # Create uploads directory if it doesn't exist
    Path(uploads_dir).mkdir(parents=True, exist_ok=True)
    
    # Save PDF (binary mode for ReportLab output)
    pdf_path = os.path.join(uploads_dir, f"{report_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)
    pdf_size = os.path.getsize(pdf_path)
    
    # Save CSV (text mode)
    csv_path = os.path.join(uploads_dir, f"{report_id}.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
    csv_size = os.path.getsize(csv_path)
    
    logger.info(f"Saved enterprise report files: PDF={pdf_size} bytes, CSV={csv_size} bytes")
    
    return pdf_path, csv_path, pdf_size, csv_size
