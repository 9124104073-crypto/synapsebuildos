"""
Full-featured generator for Synapse BuildOS Mini Project Report.
Produces:
  1. Synapse_BuildOS_Mini_Project_Report.pdf (using ReportLab 5.0+)
  2. Synapse_BuildOS_Mini_Project_Report.docx (using python-docx)
Matches the reference mini project report structure, style, page layout, and font sizing.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether, Preformatted
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

PDF_OUTPUT = "Synapse_BuildOS_Mini_Project_Report.pdf"
DOCX_OUTPUT = "Synapse_BuildOS_Mini_Project_Report.docx"

# -------------------------------------------------------------
# ReportLab Canvas with Page Numbers
# -------------------------------------------------------------
class ReportCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, num_pages):
        self.saveState()
        self.setFont("Times-Roman", 10)
        self.setFillColor(colors.black)
        # Page numbers at bottom center matching reference document: '5', '6', ...
        self.drawCentredString(306, 36, str(self._pageNumber))
        self.restoreState()


def build_pdf_report():
    print("Building PDF Report...")
    doc = SimpleDocTemplate(
        PDF_OUTPUT,
        pagesize=letter,
        leftMargin=64,
        rightMargin=64,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    p_title = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Times-Bold', fontSize=15, leading=20, alignment=TA_CENTER)
    p_sub_title = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontName='Times-Bold', fontSize=12, leading=16, alignment=TA_CENTER)
    p_meta = ParagraphStyle('DocMeta', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_CENTER)
    p_meta_bold = ParagraphStyle('DocMetaBold', parent=styles['Normal'], fontName='Times-Bold', fontSize=11, leading=15, alignment=TA_CENTER)

    ch_heading = ParagraphStyle('ChHeading', parent=styles['Normal'], fontName='Times-Bold', fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=14)
    sec_heading = ParagraphStyle('SecHeading', parent=styles['Normal'], fontName='Times-Bold', fontSize=12, leading=16, alignment=TA_LEFT, spaceBefore=8, spaceAfter=4)
    subsec_heading = ParagraphStyle('SubSecHeading', parent=styles['Normal'], fontName='Times-Bold', fontSize=11, leading=15, alignment=TA_LEFT, spaceBefore=6, spaceAfter=3)

    body = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontName='Times-Roman', fontSize=10.5, leading=14.5, alignment=TA_JUSTIFY, spaceAfter=6)
    bullet = ParagraphStyle('BulletCustom', parent=styles['Normal'], fontName='Times-Roman', fontSize=10.5, leading=14, alignment=TA_LEFT, leftIndent=16, firstLineIndent=-10, spaceAfter=3)

    tbl_hdr = ParagraphStyle('TblHdr', parent=styles['Normal'], fontName='Times-Bold', fontSize=9, leading=12, alignment=TA_CENTER)
    tbl_cell = ParagraphStyle('TblCell', parent=styles['Normal'], fontName='Times-Roman', fontSize=8.5, leading=11, alignment=TA_LEFT)
    tbl_cell_center = ParagraphStyle('TblCellCenter', parent=styles['Normal'], fontName='Times-Roman', fontSize=8.5, leading=11, alignment=TA_CENTER)

    fig_caption = ParagraphStyle('FigCaption', parent=styles['Normal'], fontName='Times-Bold', fontSize=10.5, leading=14, alignment=TA_CENTER, spaceBefore=4, spaceAfter=6)
    tbl_caption = ParagraphStyle('TblCaption', parent=styles['Normal'], fontName='Times-Bold', fontSize=10.5, leading=14, alignment=TA_CENTER, spaceBefore=4, spaceAfter=6)

    code_style = ParagraphStyle('CodeLine', parent=styles['Normal'], fontName='Courier', fontSize=7.5, leading=9.5, alignment=TA_LEFT)

    story = []

    # -------------------------------------------------------------
    # PAGE 1: COVER PAGE
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("SYNAPSE BUILDOS: GENERATIVE AI-POWERED RESIDENTIAL ARCHITECTURAL DESIGN, ESTIMATION, AND COMPLIANCE PLATFORM", p_title))
    story.append(Spacer(1, 40))
    story.append(Paragraph("A MINI PROJECT REPORT", p_sub_title))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<i>Submitted by</i>", p_meta))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>PROJECT TEAM</b><br/>(REGISTER NUMBER: 9124104073 / 9124104103 / 9124104121)", p_meta_bold))
    story.append(Spacer(1, 40))
    story.append(Paragraph("<i>in partial fulfilment for the award of the degree<br/>of</i>", p_meta))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>BACHELOR OF ENGINEERING</b><br/>IN<br/><b>COMPUTER SCIENCE AND ENGINEERING</b>", p_sub_title))
    story.append(Spacer(1, 35))
    story.append(Paragraph("<b>KCG COLLEGE OF TECHNOLOGY, KARAPAKKAM</b><br/>(AUTONOMOUS)<br/><b>NOVEMBER 2026</b>", p_meta_bold))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 2: BONAFIDE CERTIFICATE
    # -------------------------------------------------------------
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>BONAFIDE CERTIFICATE</b>", ch_heading))
    story.append(Spacer(1, 25))
    story.append(Paragraph("Certified that this mini project report <b>“SYNAPSE BUILDOS: Generative AI-Powered Residential Architectural Design, Estimation, and Compliance Platform”</b> is the bonafide work of <b>“Project Team”</b> who carried out the mini project work under my supervision.", body))
    story.append(Spacer(1, 120))

    cert_data = [
        [
            Paragraph("<b>Signature of the HOD with date</b><br/><br/><b>Dr. S. REVATHY M.E., Ph.D.,</b><br/>PROFESSOR AND HEAD,<br/>Department of Computer Science and Engineering,<br/>KCG College of Technology,<br/>Karapakkam, Chennai.", tbl_cell),
            Paragraph("<b>Signature of the Supervisor with date</b><br/><br/><b>Dr. ROBINSON JOEL</b><br/>ASSOCIATE PROFESSOR,<br/>Department of Computer Science and Engineering,<br/>KCG College of Technology,<br/>Karapakkam, Chennai.", tbl_cell)
        ]
    ]
    t_cert = Table(cert_data, colWidths=[240, 240])
    t_cert.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_cert)
    story.append(Spacer(1, 40))
    story.append(Paragraph("Certified that the above candidate(s) was examined in the End Semester mini-Project Viva-Voce Examination held on ....................................", body))
    story.append(Spacer(1, 40))

    exam_data = [
        [Paragraph("<b>INTERNAL EXAMINER</b>", tbl_cell), Paragraph("<b>EXTERNAL EXAMINER</b>", ParagraphStyle('R', parent=tbl_cell, alignment=TA_RIGHT))]
    ]
    t_exam = Table(exam_data, colWidths=[240, 240])
    story.append(t_exam)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 3: DECLARATION BY THE STUDENT
    # -------------------------------------------------------------
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>DECLARATION BY THE STUDENT</b>", ch_heading))
    story.append(Spacer(1, 30))
    story.append(Paragraph("We hereby declare that this mini project report titled <b>“SYNAPSE BUILDOS: Generative AI-Powered Residential Architectural Design, Estimation, and Compliance Platform”</b>, under the guidance of <b>“Dr. Robinson Joel”</b> is the original work done by us and we have not plagiarized or submitted to any other degree in any university by us.", body))
    story.append(Spacer(1, 180))
    story.append(Paragraph("<b>STUDENT CANDIDATES</b><br/>Department of Computer Science and Engineering<br/>KCG College of Technology, Chennai", ParagraphStyle('RR', parent=tbl_cell, alignment=TA_RIGHT)))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 4: ACKNOWLEDGEMENT
    # -------------------------------------------------------------
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>ACKNOWLEDGEMENT</b>", ch_heading))
    story.append(Spacer(1, 15))
    story.append(Paragraph("We thank the Almighty GOD for the abundant blessings showered on us. We extend our deepest love and gratitude to our dear parents who built up our career and backed us up in life.", body))
    story.append(Paragraph("We thank our management and our Principal <b>Dr. G. Prabhakaran</b> for the opportunities given to us for our career development.", body))
    story.append(Paragraph("We feel indebted to the Head of the Department <b>Dr. Revathy S</b>, Professor and Head, Department of Computer Science & Engineering, KCG College of Technology, Karapakkam, for all her encouragement, which has sustained our labor and efforts.", body))
    story.append(Paragraph("We express our deepest gratitude to the internal guide <b>Dr. Robinson Joel</b>, Associate Professor, Department of Computer Science & Engineering, KCG College of Technology, for his valuable guidance, ideas and support.", body))
    story.append(Paragraph("We would like to thank all other faculty members of Department of Computer Science & Engineering, for their help and advice throughout our life in this campus.", body))
    story.append(Paragraph("Finally, we are thankful to all our friends and all others who encouraged us and helped us in doing this project.", body))
    story.append(Spacer(1, 100))
    story.append(Paragraph("<b>PROJECT CANDIDATES</b>", ParagraphStyle('RR2', parent=tbl_cell, alignment=TA_RIGHT)))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 5: ABSTRACT
    # -------------------------------------------------------------
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>ABSTRACT</b>", ch_heading))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Synapse BuildOS</b> is an intelligent residential architectural design, cost estimation, and statutory compliance platform developed using modern web standards (HTML5, SVG, Three.js, TypeScript) and high-performance Python backend architectures (FastAPI, Pydantic, SQLAlchemy, Anthropic Claude LLM). The platform is engineered to eliminate the severe real-world disconnect between architectural drafting, civil engineering quantity estimation, and municipal bylaw approval.", body))
    story.append(Paragraph("In Synapse BuildOS, room geometry serves as the immutable single source of truth. Users can ingest project briefs from scanned documents, PDFs, or natural language prompts across English, Malayalam, Hindi, and Tamil. The system recommends pre-designed regional floor plans and provides an interactive 2D SVG plan editor where users can manipulate rooms in real coordinates (feet) on true plot boundaries with automated setback buffers. Every modification instantly updates the corresponding 3D volumetric massing model with interactive walkthroughs and sun-path simulations.", body))
    story.append(Paragraph("Crucially, Synapse BuildOS features an automated rule-verification engine that continuously evaluates designs against the <b>Tamil Nadu Combined Development and Building Rules (TNCDBR 2019)</b>, checking Floor Space Index (FSI), ground coverage, setbacks, parking provisions, room dimensions, and vertical access. Simultaneously, an arithmetic cost engine computes line-item civil estimates directly against the published <b>Tamil Nadu PWD Plinth Area Rates (2025–26)</b>, guaranteeing that cost is strictly deterministic arithmetic rather than hallucinated projections.", body))
    story.append(Paragraph("The platform aggregates these dimensions into a comprehensive <b>Construction Readiness Score (0–100)</b> spanning budget fit, regulatory compliance, buildability, and sustainability. Users can generate publication-grade PDF project dossiers and export native CAD/BIM formats (IFC4, DXF, OBJ, CSV BOQ). By unifying geometric modeling, civil engineering estimation, and generative AI copilots into a zero-build browser environment, Synapse BuildOS drastically shortens the residential pre-construction lifecycle from weeks to seconds.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 6: LIST OF TABLES
    # -------------------------------------------------------------
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>LIST OF TABLES</b>", ch_heading))
    story.append(Spacer(1, 25))

    lot_data = [
        [Paragraph("<b>TABLE NO.</b>", tbl_hdr), Paragraph("<b>TABLE NAME</b>", tbl_hdr), Paragraph("<b>PAGE NO.</b>", tbl_hdr)],
        [Paragraph("2.1", tbl_cell_center), Paragraph("Comparative Analysis of Existing Architectural & Construction Systems", tbl_cell), Paragraph("15", tbl_cell_center)],
        [Paragraph("3.4.1", tbl_cell_center), Paragraph("Tools and Technologies Used in Synapse BuildOS", tbl_cell), Paragraph("24", tbl_cell_center)],
        [Paragraph("4.1", tbl_cell_center), Paragraph("Geometric Takeoff and Rule Verification Validation Results", tbl_cell), Paragraph("30", tbl_cell_center)]
    ]
    t_lot = Table(lot_data, colWidths=[80, 320, 80])
    t_lot.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_lot)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 7: LIST OF FIGURES
    # -------------------------------------------------------------
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>LIST OF FIGURES</b>", ch_heading))
    story.append(Spacer(1, 25))

    lof_data = [
        [Paragraph("<b>FIGURE NO.</b>", tbl_hdr), Paragraph("<b>TITLE</b>", tbl_hdr), Paragraph("<b>PAGE NO.</b>", tbl_hdr)],
        [Paragraph("1.1", tbl_cell_center), Paragraph("Synapse BuildOS Platform Overview", tbl_cell), Paragraph("11", tbl_cell_center)],
        [Paragraph("3.1", tbl_cell_center), Paragraph("Synapse BuildOS System Architecture", tbl_cell), Paragraph("20", tbl_cell_center)],
        [Paragraph("3.2", tbl_cell_center), Paragraph("System Flow Diagram", tbl_cell), Paragraph("22", tbl_cell_center)],
        [Paragraph("3.3", tbl_cell_center), Paragraph("Data Flow Diagram (Level 0 Context & Level 1 Detailed DFD)", tbl_cell), Paragraph("23", tbl_cell_center)],
        [Paragraph("3.5", tbl_cell_center), Paragraph("UML Use Case Diagram", tbl_cell), Paragraph("25", tbl_cell_center)],
        [Paragraph("4.4", tbl_cell_center), Paragraph("Synapse BuildOS 3D Spatial Models (Exterior & Axonometric)", tbl_cell), Paragraph("31", tbl_cell_center)],
        [Paragraph("4.5", tbl_cell_center), Paragraph("Sample Architectural Design Model (Villa Harmony 3BHK Duplex — 2D Plan & 3D Massing)", tbl_cell), Paragraph("32", tbl_cell_center)]
    ]
    t_lof = Table(lof_data, colWidths=[80, 320, 80])
    t_lof.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t_lof)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 8: LIST OF ABBREVIATIONS
    # -------------------------------------------------------------
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>LIST OF ABBREVIATIONS</b>", ch_heading))
    story.append(Spacer(1, 25))

    abbrev_data = [
        [Paragraph("<b>AI</b>", tbl_cell), Paragraph("Artificial Intelligence", tbl_cell)],
        [Paragraph("<b>CAD</b>", tbl_cell), Paragraph("Computer-Aided Design", tbl_cell)],
        [Paragraph("<b>BIM</b>", tbl_cell), Paragraph("Building Information Modeling", tbl_cell)],
        [Paragraph("<b>AEC</b>", tbl_cell), Paragraph("Architecture, Engineering, and Construction", tbl_cell)],
        [Paragraph("<b>TNCDBR</b>", tbl_cell), Paragraph("Tamil Nadu Combined Development and Building Rules", tbl_cell)],
        [Paragraph("<b>PWD</b>", tbl_cell), Paragraph("Public Works Department (Tamil Nadu)", tbl_cell)],
        [Paragraph("<b>FSI</b>", tbl_cell), Paragraph("Floor Space Index", tbl_cell)],
        [Paragraph("<b>BOQ</b>", tbl_cell), Paragraph("Bill of Quantities", tbl_cell)],
        [Paragraph("<b>AABB</b>", tbl_cell), Paragraph("Axis-Aligned Bounding Box", tbl_cell)],
        [Paragraph("<b>SVG</b>", tbl_cell), Paragraph("Scalable Vector Graphics", tbl_cell)],
        [Paragraph("<b>API</b>", tbl_cell), Paragraph("Application Programming Interface", tbl_cell)],
        [Paragraph("<b>UI</b>", tbl_cell), Paragraph("User Interface", tbl_cell)],
        [Paragraph("<b>UX</b>", tbl_cell), Paragraph("User Experience", tbl_cell)],
        [Paragraph("<b>OCR</b>", tbl_cell), Paragraph("Optical Character Recognition", tbl_cell)],
        [Paragraph("<b>LLM</b>", tbl_cell), Paragraph("Large Language Model", tbl_cell)],
        [Paragraph("<b>REST</b>", tbl_cell), Paragraph("Representational State Transfer", tbl_cell)],
        [Paragraph("<b>IFC</b>", tbl_cell), Paragraph("Industry Foundation Classes (IFC4)", tbl_cell)],
        [Paragraph("<b>DXF</b>", tbl_cell), Paragraph("Drawing Exchange Format", tbl_cell)],
        [Paragraph("<b>ORM</b>", tbl_cell), Paragraph("Object-Relational Mapping (SQLAlchemy)", tbl_cell)]
    ]
    t_abbrev = Table(abbrev_data, colWidths=[120, 360])
    t_abbrev.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_abbrev)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 9: TABLE OF CONTENTS (Part 1)
    # -------------------------------------------------------------
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>TABLE OF CONTENTS</b>", ch_heading))
    story.append(Spacer(1, 20))

    toc_data1 = [
        [Paragraph("<b>CHAPTER NO.</b>", tbl_hdr), Paragraph("<b>TITLE</b>", tbl_hdr), Paragraph("<b>PAGE NO.</b>", tbl_hdr)],
        [Paragraph("", tbl_cell_center), Paragraph("<b>ABSTRACT</b>", tbl_cell), Paragraph("5", tbl_cell_center)],
        [Paragraph("", tbl_cell_center), Paragraph("<b>LIST OF TABLES</b>", tbl_cell), Paragraph("6", tbl_cell_center)],
        [Paragraph("", tbl_cell_center), Paragraph("<b>LIST OF FIGURES</b>", tbl_cell), Paragraph("7", tbl_cell_center)],
        [Paragraph("", tbl_cell_center), Paragraph("<b>LIST OF ABBREVIATIONS</b>", tbl_cell), Paragraph("8", tbl_cell_center)],
        [Paragraph("<b>1.</b>", tbl_cell_center), Paragraph("<b>INTRODUCTION</b>", tbl_cell), Paragraph("<b>11</b>", tbl_cell_center)],
        [Paragraph("1.1", tbl_cell_center), Paragraph("Overview", tbl_cell), Paragraph("11", tbl_cell_center)],
        [Paragraph("1.2", tbl_cell_center), Paragraph("Motivation", tbl_cell), Paragraph("12", tbl_cell_center)],
        [Paragraph("1.3", tbl_cell_center), Paragraph("Objective", tbl_cell), Paragraph("12", tbl_cell_center)],
        [Paragraph("1.4", tbl_cell_center), Paragraph("Scope", tbl_cell), Paragraph("13", tbl_cell_center)],
        [Paragraph("1.5", tbl_cell_center), Paragraph("Significance of the study", tbl_cell), Paragraph("13", tbl_cell_center)],
        [Paragraph("<b>2.</b>", tbl_cell_center), Paragraph("<b>LITERATURE SURVEY</b>", tbl_cell), Paragraph("<b>14</b>", tbl_cell_center)],
        [Paragraph("2.1", tbl_cell_center), Paragraph("Existing systems and comparative analysis", tbl_cell), Paragraph("14", tbl_cell_center)],
        [Paragraph("2.2", tbl_cell_center), Paragraph("Computational geometry and generative AI in residential CAD", tbl_cell), Paragraph("16", tbl_cell_center)],
        [Paragraph("2.3", tbl_cell_center), Paragraph("Automated building bylaw compliance and PWD estimation", tbl_cell), Paragraph("17", tbl_cell_center)],
        [Paragraph("2.4", tbl_cell_center), Paragraph("Research gap", tbl_cell), Paragraph("17", tbl_cell_center)],
        [Paragraph("<b>3.</b>", tbl_cell_center), Paragraph("<b>SYSTEM DESIGN AND IMPLEMENTATION</b>", tbl_cell), Paragraph("<b>19</b>", tbl_cell_center)],
        [Paragraph("3.1", tbl_cell_center), Paragraph("System overview", tbl_cell), Paragraph("19", tbl_cell_center)],
        [Paragraph("3.2", tbl_cell_center), Paragraph("System architecture", tbl_cell), Paragraph("19", tbl_cell_center)],
        [Paragraph("3.3", tbl_cell_center), Paragraph("System flow", tbl_cell), Paragraph("21", tbl_cell_center)]
    ]
    t_toc1 = Table(toc_data1, colWidths=[80, 320, 80])
    t_toc1.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
    ]))
    story.append(t_toc1)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 10: TABLE OF CONTENTS (Part 2)
    # -------------------------------------------------------------
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>TABLE OF CONTENTS (CONTINUED)</b>", ch_heading))
    story.append(Spacer(1, 20))

    toc_data2 = [
        [Paragraph("<b>CHAPTER NO.</b>", tbl_hdr), Paragraph("<b>TITLE</b>", tbl_hdr), Paragraph("<b>PAGE NO.</b>", tbl_hdr)],
        [Paragraph("3.4", tbl_cell_center), Paragraph("Data flow diagram (DFD)", tbl_cell), Paragraph("22", tbl_cell_center)],
        [Paragraph("3.4.1", tbl_cell_center), Paragraph("Tools and technologies used", tbl_cell), Paragraph("24", tbl_cell_center)],
        [Paragraph("3.5", tbl_cell_center), Paragraph("Use case diagram", tbl_cell), Paragraph("25", tbl_cell_center)],
        [Paragraph("3.6", tbl_cell_center), Paragraph("System modules description", tbl_cell), Paragraph("25", tbl_cell_center)],
        [Paragraph("3.7", tbl_cell_center), Paragraph("Implementation detail", tbl_cell), Paragraph("26", tbl_cell_center)],
        [Paragraph("3.8", tbl_cell_center), Paragraph("Implementation process", tbl_cell), Paragraph("27", tbl_cell_center)],
        [Paragraph("3.9", tbl_cell_center), Paragraph("Advantages of the system", tbl_cell), Paragraph("27", tbl_cell_center)],
        [Paragraph("3.10", tbl_cell_center), Paragraph("Challenges faced during implementation", tbl_cell), Paragraph("28", tbl_cell_center)],
        [Paragraph("<b>4.</b>", tbl_cell_center), Paragraph("<b>TESTING AND RESULT</b>", tbl_cell), Paragraph("<b>29</b>", tbl_cell_center)],
        [Paragraph("4.1", tbl_cell_center), Paragraph("Introduction", tbl_cell), Paragraph("29", tbl_cell_center)],
        [Paragraph("4.2", tbl_cell_center), Paragraph("Types of testing", tbl_cell), Paragraph("29", tbl_cell_center)],
        [Paragraph("4.3", tbl_cell_center), Paragraph("Testing procedures", tbl_cell), Paragraph("30", tbl_cell_center)],
        [Paragraph("4.4", tbl_cell_center), Paragraph("Results", tbl_cell), Paragraph("31", tbl_cell_center)],
        [Paragraph("4.5", tbl_cell_center), Paragraph("Conclusion of testing", tbl_cell), Paragraph("32", tbl_cell_center)],
        [Paragraph("<b>5.</b>", tbl_cell_center), Paragraph("<b>CONCLUSION AND FUTURE WORK</b>", tbl_cell), Paragraph("<b>33</b>", tbl_cell_center)],
        [Paragraph("5.1", tbl_cell_center), Paragraph("Conclusion", tbl_cell), Paragraph("33", tbl_cell_center)],
        [Paragraph("5.2", tbl_cell_center), Paragraph("Future work", tbl_cell), Paragraph("34", tbl_cell_center)],
        [Paragraph("", tbl_cell_center), Paragraph("<b>APPENDIX 1: SAMPLE CODE</b>", tbl_cell), Paragraph("<b>35</b>", tbl_cell_center)],
        [Paragraph("", tbl_cell_center), Paragraph("<b>REFERENCES</b>", tbl_cell), Paragraph("<b>48</b>", tbl_cell_center)]
    ]
    t_toc2 = Table(toc_data2, colWidths=[80, 320, 80])
    t_toc2.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_toc2)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 11: CHAPTER 1 - INTRODUCTION (1.1 Overview & Figure 1.1)
    # -------------------------------------------------------------
    story.append(Paragraph("<b>CHAPTER 1</b>", ch_heading))
    story.append(Paragraph("<b>INTRODUCTION</b>", ch_heading))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>1.1 OVERVIEW</b>", sec_heading))
    story.append(Paragraph("<b>Synapse BuildOS</b> is an intelligent, full-stack architectural design, estimation, and statutory compliance platform developed using modern web technologies (HTML5, Scalable Vector Graphics, JavaScript/TypeScript, Three.js) and Python backend computational frameworks (FastAPI, Pydantic, SQLAlchemy, Anthropic Claude). It is explicitly designed to eliminate the historical divide between architectural drafting, civil engineering cost estimation, and municipal regulatory approval.", body))
    story.append(Paragraph("In conventional residential construction, drafting a floor plan in AutoCAD, calculating quantity takeoff in Microsoft Excel, and verifying compliance against local municipal building codes (such as the Tamil Nadu Combined Development and Building Rules, TNCDBR 2019) are conducted by separate professionals in isolated silos. When a client requests a modification—such as expanding a master bedroom or moving a living room partition—the entire cycle of drafting, structural resizing, cost re-estimation, and bylaw checking must be manually repeated. This latency causes severe budget overruns, project delays, and frequent statutory rejections.", body))
    story.append(Paragraph("Synapse BuildOS resolves this systemic friction by establishing <b>room geometry as the single source of truth</b>. A room is modeled as an atomic rectangle with spatial coordinates defined in feet. From these exact rectangles, built-up areas, wall surface areas, door and window schedules, Floor Space Index (FSI), plot coverage, setback buffers, PWD plinth-area construction costs, and 3D volumetric models are computed instantaneously and deterministically.", body))
    story.append(Spacer(1, 6))

    if os.path.exists('report_assets/fig1_1_synapse_overview.png'):
        im_fig1 = Image('report_assets/fig1_1_synapse_overview.png', width=420, height=280)
        story.append(im_fig1)
        story.append(Paragraph("Figure 1.1: Synapse BuildOS Platform Overview", fig_caption))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 12: 1.2 MOTIVATION & 1.3 OBJECTIVE
    # -------------------------------------------------------------
    story.append(Paragraph("<b>1.2 MOTIVATION</b>", sec_heading))
    story.append(Paragraph("Many homeowners and prospective builders in India undertake residential construction without direct, real-time access to professional architectural planning and compliance advice. Commercial CAD software like AutoCAD and Revit require steep learning curves and expensive licensing, while consumer floor-plan tools remain purely cosmetic, lacking any understanding of local statutory building codes or regional construction rate schedules.", body))
    story.append(Paragraph("The primary motivation behind Synapse BuildOS is to provide architects, contractors, and homeowners with an accessible, unified residential building intelligence platform. By combining computational 2D/3D geometry, deterministic civil engineering quantity estimation, and generative AI copilot assistance, the system allows non-technical users to explore viable house layouts with immediate, trusted feedback on budget feasibility and legal compliance.", body))
    story.append(Paragraph("Key motivation factors include:", body))
    story.append(Paragraph("• Eliminating the disconnect between architectural design and cost estimation.", bullet))
    story.append(Paragraph("• Preventing municipal building plan rejections by enforcing TNCDBR 2019 rules in real time.", bullet))
    story.append(Paragraph("• Providing deterministic, auditable cost estimation based on published Tamil Nadu PWD rates.", bullet))
    story.append(Paragraph("• Supporting natural language design modifications through multi-lingual AI prompts.", bullet))
    story.append(Paragraph("• Offering a zero-install, browser-based CAD and 3D walkthrough experience.", bullet))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>1.3 OBJECTIVE</b>", sec_heading))
    story.append(Paragraph("The primary technical objectives of the project are as follows:", body))
    story.append(Paragraph("1. To establish a unified geometric data model where 2D SVG rectangles serve as the single source of truth for all spatial, structural, and cost metrics.", bullet))
    story.append(Paragraph("2. To develop an automated statutory compliance engine that validates residential designs against the Tamil Nadu Combined Development and Building Rules (TNCDBR 2019).", bullet))
    story.append(Paragraph("3. To implement a deterministic quantity takeoff and cost estimation engine based on the published Tamil Nadu PWD Plinth Area Rates (2025–26).", bullet))
    story.append(Paragraph("4. To generate real-time 3D parametric massing models and first-person walkthroughs using Three.js directly in the browser.", bullet))
    story.append(Paragraph("5. To integrate a multi-lingual Large Language Model assistant (Cortex AI) capable of translating conversational client requests into valid geometric adjustments.", bullet))
    story.append(Paragraph("6. To compute a comprehensive Construction Readiness Score (0–100) and export professional CAD/BIM assets (IFC4, DXF, OBJ, CSV BOQ, and PDF reports).", bullet))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 13: 1.4 SCOPE & 1.5 SIGNIFICANCE OF THE STUDY
    # -------------------------------------------------------------
    story.append(Paragraph("<b>1.4 SCOPE</b>", sec_heading))
    story.append(Paragraph("The scope of the Synapse BuildOS project encompasses:", body))
    story.append(Paragraph("• Design and development of a full-stack, browser-based residential CAD studio.", bullet))
    story.append(Paragraph("• Support for residential building typologies (villas, bungalows, compact urban houses, row housing) up to Ground + 2 floors.", bullet))
    story.append(Paragraph("• Ingestion of client briefs via scanned documents, images, PDFs (using OCR), and freeform text.", bullet))
    story.append(Paragraph("• Real-time 2D floor plan editing with live collision detection and setback boundaries.", bullet))
    story.append(Paragraph("• Interactive 3D spatial rendering, material swatches, door/window punch-outs, and sun-path lighting.", bullet))
    story.append(Paragraph("• Automated TNCDBR 2019 checks covering FSI, ground coverage, front/rear/side setbacks, room aspect ratios, and parking.", bullet))
    story.append(Paragraph("• Real-time civil budget calculation incorporating structural RCC frame, masonry, finishes, plumbing, and electrical points.", bullet))

    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>1.5 SIGNIFICANCE OF THE STUDY</b>", sec_heading))
    story.append(Paragraph("• <b>Democratization of Architectural Intelligence:</b> Enables homeowners to participate actively in the design of their living spaces while understanding cost and legal ramifications.", bullet))
    story.append(Paragraph("• <b>Zero Re-work and Cost Predictability:</b> Changes to room boundaries reflect immediately across quantity takeoff and PWD pricing, eliminating post-tender budget escalation.", bullet))
    story.append(Paragraph("• <b>Statutory Compliance Assurance:</b> Proactive violation flags prevent costly penalties, plan submission rejections, and structural demolition risks.", bullet))
    story.append(Paragraph("• <b>AEC Stakeholder Consensus:</b> Provides role-based views where owners, architects, and contractors share the identical data model without version confusion.", bullet))
    story.append(Paragraph("• <b>Advancement in Applied AI:</b> Demonstrates how generative LLMs can be constrained by deterministic geometric rules to provide reliable, hallucination-free CAD modifications.", bullet))
    story.append(Paragraph("• <b>Interoperability:</b> Bridges consumer web applications with professional AEC workflows through standard IFC4 and DXF exports.", bullet))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 14: CHAPTER 2 - LITERATURE SURVEY (2.1 Existing Systems)
    # -------------------------------------------------------------
    story.append(Paragraph("<b>CHAPTER 2</b>", ch_heading))
    story.append(Paragraph("<b>LITERATURE SURVEY</b>", ch_heading))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>2.1 EXISTING SYSTEMS AND COMPARATIVE ANALYSIS</b>", sec_heading))
    story.append(Paragraph("Computer-Aided Design (CAD) and Building Information Modeling (BIM) tools have traditionally focused on high-precision geometric drafting for trained professionals. Commercial platforms such as Autodesk AutoCAD and Revit provide comprehensive drafting suites but require extensive training, specialized workstations, and costly subscriptions. Crucially, these desktop tools lack native awareness of regional Indian municipal bylaws and do not incorporate localized government rate schedules.", body))
    story.append(Paragraph("Consumer-oriented web tools such as Planner 5D, RoomSketcher, and Sweet Home 3D allow non-professionals to create 2D and 3D floor plans. However, these tools operate purely at a visual and decorative level. They treat walls as abstract graphics rather than structural assemblies, cannot calculate structural civil quantities, and have no capability to verify municipal setbacks or zoning regulations.", body))
    story.append(Paragraph("Recent advancements in generative AI for architecture (e.g., Finch 3D, Hypar, and generative floor plan research models) employ machine learning to generate spatial layouts. However, most generative research models generate raster images or unconstrained vector geometry that frequently produce overlapping rooms, unbuildable structural configurations, and hallucinated dimensions. They lack deterministic compliance verification against statutory codes such as the Tamil Nadu Combined Development and Building Rules (TNCDBR 2019).", body))
    story.append(Paragraph("Synapse BuildOS addresses these limitations by introducing a hybrid architecture: a deterministic geometric kernel that computes exact arithmetic for cost and bylaws, paired with a constrained LLM copilot that operates exclusively through validated schema transformations.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 15: TABLE 2.1 - COMPARATIVE ANALYSIS
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Table 2.1: Comparative Analysis of Existing Architectural & Estimation Systems</b>", tbl_caption))
    story.append(Spacer(1, 10))

    comp_data = [
        [Paragraph("<b>Existing System</b>", tbl_hdr), Paragraph("<b>Target Audience</b>", tbl_hdr), Paragraph("<b>Type</b>", tbl_hdr), Paragraph("<b>Key Features</b>", tbl_hdr), Paragraph("<b>Limitations</b>", tbl_hdr), Paragraph("<b>Remarks</b>", tbl_hdr)],
        [
            Paragraph("AutoCAD / Revit", tbl_cell),
            Paragraph("Architects, structural engineers", tbl_cell),
            Paragraph("Desktop CAD / BIM Suite", tbl_cell),
            Paragraph("High-precision drafting, 3D modeling, construction docs", tbl_cell),
            Paragraph("Steep learning curve, high cost, no Indian municipal bylaw rules", tbl_cell),
            Paragraph("Industry standard drafting, not accessible for rapid decisions", tbl_cell)
        ],
        [
            Paragraph("Planner 5D / RoomSketcher", tbl_cell),
            Paragraph("Homeowners, interior decorators", tbl_cell),
            Paragraph("Consumer Web / Mobile App", tbl_cell),
            Paragraph("Drag-and-drop 2D/3D layouts, furniture catalogue", tbl_cell),
            Paragraph("Purely visual; no civil costing, no bylaw compliance checking", tbl_cell),
            Paragraph("Good for interior visualization, inadequate for building approvals", tbl_cell)
        ],
        [
            Paragraph("Finch 3D / Hypar", tbl_cell),
            Paragraph("Enterprise developers, computational architects", tbl_cell),
            Paragraph("Generative BIM Platform", tbl_cell),
            Paragraph("Algorithmic massing, daylight optimization", tbl_cell),
            Paragraph("Geared for commercial high-rises; lacks Indian regional PWD costing", tbl_cell),
            Paragraph("Advanced generative tool, but disconnected from local Indian regulations", tbl_cell)
        ],
        [
            Paragraph("<b>Synapse BuildOS (Proposed)</b>", tbl_cell),
            Paragraph("<b>Homeowners, architects, local builders</b>", tbl_cell),
            Paragraph("<b>Web-based Building Intelligence OS</b>", tbl_cell),
            Paragraph("<b>Single source of truth, 2D SVG, 3D Three.js, live TNCDBR & PWD cost</b>", tbl_cell),
            Paragraph("<b>Focused on residential typologies up to G+2</b>", tbl_cell),
            Paragraph("<b>Zero-install, deterministic, auditable, and accessible to all AEC users</b>", tbl_cell)
        ]
    ]

    t_comp = Table(comp_data, colWidths=[75, 75, 70, 95, 95, 74])
    t_comp.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#f0fdf4')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_comp)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 16: 2.2 COMPUTATIONAL GEOMETRY & GENERATIVE AI IN CAD
    # -------------------------------------------------------------
    story.append(Paragraph("<b>2.2 COMPUTATIONAL GEOMETRY AND GENERATIVE AI IN RESIDENTIAL CAD</b>", sec_heading))
    story.append(Paragraph("Computational geometry serves as the foundational backbone for Computer-Aided Architectural Design. In architectural space planning, floor plans can be conceptualized as planar graphs where rooms represent vertices and shared partitions represent edges. However, maintaining geometric integrity during dynamic user editing introduces challenging computational problems, particularly in collision detection, boundary clipping, and spatial adjacency.", body))
    story.append(Paragraph("Synapse BuildOS implements an Axis-Aligned Bounding Box (AABB) sweep-and-prune algorithm operating with a calibrated 0.05 ft tolerance. This allows the system to instantaneously detect invalid room overlaps while permitting adjacent rooms to share common partition walls without computational ambiguity. When rooms share an edge, the takeoff engine assigns a 0.5 weighting to the partition run, ensuring that shared walls are not double-counted in civil brickwork estimates.", body))
    story.append(Paragraph("Recent advances in Large Language Models (LLMs) have enabled conversational software interactions. However, unconstrained LLMs cannot perform reliable spatial reasoning and frequently output geometrically invalid or self-intersecting polygons. In Synapse BuildOS, the generative AI subsystem (Cortex) is decoupled from direct geometric creation. Instead of drawing lines, Claude generates high-level structured mutations (e.g., 'expand_room', 'split_space', 'swap_finishes') validated against strict Pydantic schemas.", body))
    story.append(Paragraph("These mutations are subsequently passed through the deterministic geometry kernel, which executes the required coordinate transformations, verifies boundary constraints, and recalculates engineering quantities before presenting the updated design to the user.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 17: 2.3 BYLAW COMPLIANCE & 2.4 RESEARCH GAP
    # -------------------------------------------------------------
    story.append(Paragraph("<b>2.3 AUTOMATED BUILDING BYLAW COMPLIANCE AND PWD ESTIMATION</b>", sec_heading))
    story.append(Paragraph("Statutory compliance verification in Indian civil engineering has traditionally been a manual, post-design inspection process. The <b>Tamil Nadu Combined Development and Building Rules (TNCDBR 2019)</b> govern all residential construction within the state, mandating specific geometric constraints based on plot size, road width, and building height. Rules dictate minimum front, rear, and side setbacks, permissible Floor Space Index (FSI), maximum ground coverage, mandatory vehicle parking dimensions, and minimum habitable room areas.", body))
    story.append(Paragraph("Manual checking of these clauses is prone to human error and frequently delays municipal approvals. Synapse BuildOS codifies the TNCDBR 2019 residential provisions into deterministic mathematical evaluation rules. Every time a room is dragged or resized, the engine re-evaluates setbacks against plot boundaries, recalculates total built-up area and FSI, checks room aspect ratios, and highlights non-compliant conditions with exact numerical margins.", body))
    story.append(Paragraph("Similarly, construction budgeting is commonly distorted by subjective contractor markups. Synapse BuildOS anchors all financial estimation in the published <b>Tamil Nadu Public Works Department (TN PWD) Schedule of Rates (2025–26)</b>. By calculating exact plinth areas, perimeter wall runs, structural RCC column-beam grids, flooring surfaces, and door/window counts, the cost engine applies published government rates line by line, providing an auditable, transparent estimate that can be verified by hand.", body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>2.4 RESEARCH GAP</b>", sec_heading))
    story.append(Paragraph("Despite recent software advancements, significant research gaps persist in architectural CAD:", body))
    story.append(Paragraph("1. <b>Fragmented Workflows:</b> CAD drafting, quantity estimation, and municipal compliance operate as disconnected tools, causing severe information loss between stages.", bullet))
    story.append(Paragraph("2. <b>Lack of Regional Statutory Rules:</b> Mainstream CAD engines do not encode Indian municipal building rules (TNCDBR, NBC), leaving compliance to manual checking.", bullet))
    story.append(Paragraph("3. <b>Opaque Financial Projections:</b> Existing tools lack integration with authoritative public rate schedules (PWD), leading to untrusted cost projections.", bullet))
    story.append(Paragraph("4. <b>Unreliable Generative AI:</b> Generative image models hallucinate unbuildable plans without structural, dimensional, or legal validity.", bullet))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 18: KEY LIMITATIONS OBSERVED IN EXISTING SYSTEMS
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>KEY LIMITATIONS OBSERVED IN EXISTING SYSTEMS</b>", sec_heading))
    story.append(Spacer(1, 10))
    story.append(Paragraph("An analysis of current industry practices reveals the following primary bottlenecks:", body))
    story.append(Paragraph("1. <b>Technical Complexity:</b> Advanced CAD and BIM platforms require years of professional training, alienating homeowners and small contractors from direct participation in the design loop.", bullet))
    story.append(Paragraph("2. <b>Delayed Feedback Loops:</b> Design revisions take days or weeks to be manually re-costed and re-checked for compliance, slowing project initiation.", bullet))
    story.append(Paragraph("3. <b>Absence of Single Source of Truth:</b> Floor plans, 3D presentations, and BOQ spreadsheets frequently disagree because they are maintained in disparate files.", bullet))
    story.append(Paragraph("4. <b>High Risk of Statutory Rejection:</b> Violations of municipal setbacks and FSI limits are often discovered only during formal municipal plan scrutiny, necessitating expensive structural redesigns.", bullet))
    story.append(Paragraph("5. <b>High Cost of Software Access:</b> Enterprise drafting packages impose recurring per-seat licensing fees that are prohibitive for small building practices.", bullet))
    story.append(Paragraph("6. <b>Language Barriers:</b> Available architectural tools are exclusively English-centric, hindering effective collaboration with regional clients and on-site contractors.", body))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>The Synapse BuildOS Solution:</b> Synapse BuildOS addresses each of these gaps by offering a unified, zero-install web platform that couples deterministic geometric modeling with automated TNCDBR bylaw verification, PWD plinth-area rate calculation, multi-lingual AI assistance, and open CAD/BIM data portability.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 19: CHAPTER 3 - SYSTEM DESIGN & IMPLEMENTATION
    # -------------------------------------------------------------
    story.append(Paragraph("<b>CHAPTER 3</b>", ch_heading))
    story.append(Paragraph("<b>SYSTEM DESIGN AND IMPLEMENTATION</b>", ch_heading))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>3.1 SYSTEM OVERVIEW</b>", sec_heading))
    story.append(Paragraph("<b>Synapse BuildOS</b> is structured around a centralized geometric state engine where all spatial, structural, compliance, and financial metrics are derived from a single array of room rectangles. The system features a responsive dual-surface architecture:", body))
    story.append(Paragraph("1. <b>Landing Page & Project Brief Configurator:</b> Ingests user requirements (plot dimensions, budget ceiling, room count, architectural style) through interactive forms, document upload (OCR), or conversational voice prompts.", body))
    story.append(Paragraph("2. <b>Visual CAD Studio:</b> A full-featured design workspace providing interactive 2D SVG plan editing, real-time Three.js 3D extrusion, live TNCDBR 2019 compliance auditing, line-item PWD cost breakdown, and one-click PDF dossier generation.", body))
    story.append(Paragraph("Because the coordinate space in the SVG canvas uses feet as its native units, the visual representation is mathematically identical to the internal analytical model. No translation layers exist to introduce rounding errors or coordinate drift.", body))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>3.2 SYSTEM ARCHITECTURE</b>", sec_heading))
    story.append(Paragraph("Synapse BuildOS implements a multi-tiered architecture comprising five coordinated subsystems:", body))
    story.append(Paragraph("• <b>User Interface Layer:</b> Built with HTML5, CSS3, SVG, and Vanilla JavaScript / React, requiring zero bundler toolchain dependencies. It executes high-speed pointer-driven canvas operations at 60 FPS.", bullet))
    story.append(Paragraph("• <b>Client-Side Engine Kernel (web/engine.js):</b> Contains the shared mathematical model, geometry takeoff routines, TNCDBR compliance predicates, and PWD cost formulas.", bullet))
    story.append(Paragraph("• <b>FastAPI Backend Services:</b> High-throughput Python microservices providing authentication, persistent project storage, PDF dossier compilation, and CAD/BIM exporters (IFC4, DXF).", bullet))
    story.append(Paragraph("• <b>Generative Intelligence (Cortex AI):</b> Powered by Anthropic Claude 3.5, providing conversational design guidance, multi-lingual translation, and rule-constrained plan mutation.", bullet))
    story.append(Paragraph("• <b>Data Persistence:</b> SQLite database for development and PostgreSQL for production, managed through SQLAlchemy 2.0 ORM with Redis caching.", bullet))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 20: FIGURE 3.1 - SYSTEM ARCHITECTURE DIAGRAM
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))
    if os.path.exists('report_assets/fig3_1_clean.png'):
        im_arch = Image('report_assets/fig3_1_clean.png', width=440, height=316)
        story.append(im_arch)
        story.append(Paragraph("Figure 3.1: Synapse BuildOS System Architecture", fig_caption))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Figure 3.1 illustrates the comprehensive system architecture of Synapse BuildOS. The architecture enforces strict separation of concerns across AEC stakeholders (Owner, Architect, Contractor), the browser execution environment, the shared mathematical model, and the server-side computational engines. By maintaining the room rectangles as the authoritative atom of state, all client-side viewports and server-side analysis microservices remain perfectly synchronized.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 21: 3.3 SYSTEM FLOW
    # -------------------------------------------------------------
    story.append(Paragraph("<b>3.3 SYSTEM FLOW</b>", sec_heading))
    story.append(Paragraph("The end-to-end operational workflow of Synapse BuildOS proceeds across nine distinct stages:", body))
    story.append(Paragraph("1. <b>Start Application:</b> The user initializes the Synapse BuildOS studio in any modern browser without requiring plugin installations or local drafting software.", body))
    story.append(Paragraph("2. <b>Input Client Brief:</b> The user defines plot dimensions (width and depth in feet), budget ceiling, target location (e.g., Chennai, Coimbatore, Kochi), and required room typologies via text or document upload.", body))
    story.append(Paragraph("3. <b>Select Recommended Plan:</b> The recommendation engine queries the library of pre-engineered typologies and selects the layout with the highest match score against plot and family criteria.", body))
    story.append(Paragraph("4. <b>Render 2D Plan Geometry:</b> The system renders the floor plan on an SVG canvas in feet, automatically drawing municipal setback boundaries, room rectangles, and partition walls.", body))
    story.append(Paragraph("5. <b>Extrude 3D Spatial Walkthrough:</b> The Three.js pipeline extrudes 2D room boundaries into 3D massing blocks, procedural wall textures, fenestrations (doors/windows), and realistic ambient lighting.", body))
    story.append(Paragraph("6. <b>Compute Geometric Takeoff:</b> The geometry kernel calculates exact built-up area, ground footprint, perimeter wall surface runs, flooring area, and opening deductions.", body))
    story.append(Paragraph("7. <b>Evaluate Compliance & PWD Cost:</b> The system checks TNCDBR 2019 rules (setbacks, coverage, FSI, height) and calculates construction cost line by line against the published TN PWD schedule.", body))
    story.append(Paragraph("8. <b>Calculate Construction Readiness Score:</b> The scoring module synthesizes budget fit, compliance, buildability, and sustainability into a 0–100 readiness index.", body))
    story.append(Paragraph("9. <b>Generate Dossier & Export CAD/BIM:</b> The user exports production assets including PDF architectural reports, IFC4 BIM files, 2D DXF CAD drawings, OBJ 3D meshes, and CSV BOQ schedules.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 22: FIGURE 3.2 - SYSTEM FLOW DIAGRAM & 3.4 DFD INTRO
    # -------------------------------------------------------------
    if os.path.exists('report_assets/final_fig3_2_flowchart_clean.png'):
        im_flow = Image('report_assets/final_fig3_2_flowchart_clean.png', width=370, height=274)
        story.append(im_flow)
        story.append(Paragraph("Figure 3.2: System Flow Diagram", fig_caption))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>3.4 DATA FLOW DIAGRAM (DFD)</b>", sec_heading))
    story.append(Paragraph("The Data Flow Diagram illustrates how spatial data, user modifications, and statutory rate cards traverse the Synapse BuildOS system across conceptual and detailed levels.", body))
    story.append(Paragraph("<b>Level 0: Context Diagram:</b> The user (Homeowner, Architect, or Contractor) supplies brief parameters, spatial adjustments, and AI prompts to the Synapse BuildOS core engine. The system processes these inputs and returns real-time 2D/3D visualizations, TNCDBR compliance audit checklists, PWD cost estimates, and CAD/BIM export packages.", body))
    story.append(Paragraph("<b>Level 1: Detailed DFD:</b> The system deconstructs data flow into discrete functional transformations: Brief Ingestion (1.0), 2D SVG Modeling (2.0), 3D Massing Extrusion (3.0), Compliance Verification (4.0), Cost Takeoff (5.0), and Readiness Scoring (6.0), coordinated with live databases and rate cards.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 23: FIGURE 3.3 - DATA FLOW DIAGRAM (LEVEL 0 & LEVEL 1)
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))
    if os.path.exists('report_assets/fig3_3_synapse_dfd.png'):
        im_dfd = Image('report_assets/fig3_3_synapse_dfd.png', width=420, height=311)
        story.append(im_dfd)
        story.append(Paragraph("Figure 3.3: Data Flow Diagram (Level 0 & Level 1)", fig_caption))

    story.append(Spacer(1, 8))
    story.append(Paragraph("As shown in Figure 3.3, Level 0 models the external interaction boundaries between users and the core engine. Level 1 maps internal information flows between processes and primary data stores: <b>D1 (Project DB)</b>, <b>D2 (PWD Rate Cards & TNCDBR Rules)</b>, and <b>D3 (Plan Library)</b>. Because each process queries standardized data models, calculations remain fully deterministic.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 24: TABLE 3.4.1 - TOOLS AND TECHNOLOGIES USED
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>3.4.1 TOOLS AND TECHNOLOGIES USED</b>", sec_heading))
    story.append(Spacer(1, 10))

    tech_data = [
        [Paragraph("<b>Component</b>", tbl_hdr), Paragraph("<b>Technology Used</b>", tbl_hdr), Paragraph("<b>Description</b>", tbl_hdr)],
        [Paragraph("Front-end Architecture", tbl_cell), Paragraph("HTML5, CSS3, Vanilla JS / TypeScript, SVG", tbl_cell), Paragraph("Builds the responsive, zero-build web interface and 2D canvas editor", tbl_cell)],
        [Paragraph("3D Graphics & Walkthrough", tbl_cell), Paragraph("Three.js r160, WebGL", tbl_cell), Paragraph("Renders procedural 3D massing, materials, first-person camera, and sun shadows", tbl_cell)],
        [Paragraph("Document Processing / OCR", tbl_cell), Paragraph("Tesseract.js, PDF.js", tbl_cell), Paragraph("Extracts client briefs, plot dimensions, and space requirements from scanned files", tbl_cell)],
        [Paragraph("Geometric Engine", tbl_cell), Paragraph("JavaScript (web/engine.js) & Python Shapely", tbl_cell), Paragraph("Executes AABB collision detection, area takeoff, and perimeter wall calculations", tbl_cell)],
        [Paragraph("Compliance Engine", tbl_cell), Paragraph("JavaScript / Python", tbl_cell), Paragraph("Evaluates rules against Tamil Nadu Combined Development & Building Rules (TNCDBR 2019)", tbl_cell)],
        [Paragraph("Cost Estimation Engine", tbl_cell), Paragraph("Python / JavaScript", tbl_cell), Paragraph("Computes line-item civil estimates based on published TN PWD 2025–26 rates", tbl_cell)],
        [Paragraph("Backend Framework", tbl_cell), Paragraph("FastAPI, Python 3.11+", tbl_cell), Paragraph("High-speed REST API for project management, exports, and LLM orchestration", tbl_cell)],
        [Paragraph("Database & ORM", tbl_cell), Paragraph("SQLite / PostgreSQL, SQLAlchemy 2.0", tbl_cell), Paragraph("Persists projects, immutable snapshots, audit logs, and regional rate cards", tbl_cell)],
        [Paragraph("AI Copilot Subsystem", tbl_cell), Paragraph("Anthropic Claude 3.5 Sonnet (Cortex Engine)", tbl_cell), Paragraph("Translates multi-lingual voice/text prompts into validated schema mutations", tbl_cell)],
        [Paragraph("CAD/BIM Export Engine", tbl_cell), Paragraph("IfcOpenShell, DXF Generator", tbl_cell), Paragraph("Exports industry-standard IFC4 building models and AutoCAD DXF drawings", tbl_cell)],
        [Paragraph("Development IDE & VCS", tbl_cell), Paragraph("Visual Studio Code, Git, GitHub", tbl_cell), Paragraph("Used for version control, continuous integration, and collaborative development", tbl_cell)]
    ]

    t_tech = Table(tech_data, colWidths=[100, 140, 240])
    t_tech.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_tech)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 25: 3.5 USE CASE DIAGRAM & 3.6 SYSTEM MODULES INTRO
    # -------------------------------------------------------------
    story.append(Paragraph("<b>3.5 USE CASE DIAGRAM</b>", sec_heading))
    story.append(Paragraph("The Use Case Diagram depicts the functional interactions between system actors (Homeowner/Client, Architect/Designer, Contractor/Estimator) and the Synapse BuildOS platform.", body))

    if os.path.exists('report_assets/final_fig3_5_usecase_clean.png'):
        im_uc = Image('report_assets/final_fig3_5_usecase_clean.png', width=420, height=311)
        story.append(im_uc)
        story.append(Paragraph("Figure 3.5: Use case diagram", fig_caption))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Actors and Roles:</b>", subsec_heading))
    story.append(Paragraph("• <b>Homeowner (Client):</b> Submits briefs, explores recommended layouts, inspects budget fit, and takes 3D walkthroughs.", bullet))
    story.append(Paragraph("• <b>Architect (Designer):</b> Manipulates room geometry, configures fenestrations, verifies TNCDBR bylaws, and executes AI prompt adjustments.", bullet))
    story.append(Paragraph("• <b>Contractor (Builder):</b> Reviews line-item PWD civil estimates, inspects structural takeoffs, and downloads BOQ spreadsheets.", bullet))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 26: 3.6 SYSTEM MODULES DESCRIPTION (Modules 1 to 3)
    # -------------------------------------------------------------
    story.append(Paragraph("<b>3.6 SYSTEM MODULES DESCRIPTION</b>", sec_heading))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>3.6.1 CLIENT BRIEF AND PROJECT INGESTION MODULE</b>", subsec_heading))
    story.append(Paragraph("This module handles project intake through multiple modalities. It supports structured form inputs, natural language descriptions, and scanned document ingestion. Optical Character Recognition (OCR) powered by Tesseract.js extracts key parameters from client brief documents—such as plot frontage, depth, road width, budget limit, and required bedroom counts. The recommendation engine evaluates library typologies against these criteria to suggest optimal starting layouts.", body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>3.6.2 2D PLAN GEOMETRY AND SPACE ENGINE MODULE</b>", subsec_heading))
    story.append(Paragraph("The 2D geometry engine manages spatial layouts directly in Scalable Vector Graphics (SVG). The SVG coordinate system operates in feet, eliminating scale conversion distortions. Users can add, resize, drag, or delete rooms across multiple floors. The engine executes continuous Axis-Aligned Bounding Box (AABB) overlap detection to prevent invalid spatial intersections while intelligently recognizing and half-weighting shared partition walls.", body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>3.6.3 3D SPATIAL MASSING AND WALKTHROUGH MODULE</b>", subsec_heading))
    story.append(Paragraph("The 3D module leverages Three.js r160 to procedurally extrude 2D floor plans into three-dimensional architectural massing blocks. Floor slabs, exterior walls, interior partitions, doors, and windows are constructed programmatically. Procedural canvas textures generate high-fidelity surface finishes without external asset dependencies. Users can alternate between OrbitControls for isometric inspection and PointerLockControls for immersive first-person interior walkthroughs.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 27: MODULES 4-6 & 3.7 IMPLEMENTATION DETAILS
    # -------------------------------------------------------------
    story.append(Paragraph("<b>3.6.4 TNCDBR COMPLIANCE VERIFICATION MODULE</b>", subsec_heading))
    story.append(Paragraph("This module provides automated statutory validation against the <b>Tamil Nadu Combined Development and Building Rules (TNCDBR 2019)</b>. It computes real-time front, rear, and side setbacks relative to plot boundaries, checks maximum permissible Floor Space Index (FSI) and ground coverage, verifies minimum habitable room sizes (e.g., minimum 100 sq ft for bedrooms), checks ventilation ratios, and confirms vehicle parking provisions.", body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>3.6.5 PWD PLINTH-AREA COST ESTIMATION MODULE</b>", subsec_heading))
    story.append(Paragraph("The cost engine applies the published <b>Tamil Nadu PWD Plinth Area Rates (2025–26)</b>. It performs automated quantity takeoff across structural civil components: RCC framed structure, brick masonry, plastering, premium flooring (vitrified tile/granite), wall finishes, electrical points, and plumbing fixtures. Every line item is calculated transparently from room geometry rather than statistical approximations.", body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>3.6.6 CONSTRUCTION READINESS SCORING & EXPORT MODULE</b>", subsec_heading))
    story.append(Paragraph("Synthesizes overall design feasibility into a 0–100 Readiness Score based on four weighted pillars: Budget Fit (35%), Bylaw Compliance (35%), Buildability (15%), and Sustainability (15%). It generates publication-grade PDF dossiers and exports industry-standard CAD/BIM assets: IFC4, DXF, OBJ, and CSV BOQ.", body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>3.7 IMPLEMENTATION DETAILS</b>", sec_heading))
    story.append(Paragraph("The geometric takeoff formulas implemented in the engine kernel are mathematically defined as:", body))
    story.append(Paragraph("• <b>Built-up Area:</b> A_built = Σ Area(r)  [for all r.type ∉ {parking, balcony}]", bullet))
    story.append(Paragraph("• <b>Ground Footprint:</b> A_footprint = Σ Area(r)  [for all r.floor == 0]", bullet))
    story.append(Paragraph("• <b>Wall Surface Area:</b> A_wall = Σ Perimeter(r) × 10ft × (1 − 0.12) × 0.5", bullet))
    story.append(Paragraph("• <b>Floor Space Index:</b> FSI = A_built / A_plot", bullet))
    story.append(Paragraph("• <b>Ground Coverage:</b> Coverage = A_footprint / A_plot", bullet))
    story.append(Paragraph("The constant 0.12 accounts for standard fenestration deductions, while the 0.5 factor prevents double-counting of shared partition walls.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 28: 3.8 IMPLEMENTATION PROCESS, 3.9 ADVANTAGES, 3.10 CHALLENGES
    # -------------------------------------------------------------
    story.append(Paragraph("<b>3.8 IMPLEMENTATION PROCESS</b>", sec_heading))
    story.append(Paragraph("The implementation lifecycle followed six structured engineering phases:", body))
    story.append(Paragraph("1. <b>Requirement Analysis:</b> Codified TNCDBR 2019 clauses, PWD plinth schedules, and residential room typologies into formal data specifications.", bullet))
    story.append(Paragraph("2. <b>System Architecture Design:</b> Designed the unified single-source-of-truth data model, SVG-in-feet coordinate mapping, and REST API schemas.", bullet))
    story.append(Paragraph("3. <b>Core Engine Development:</b> Implemented geometric takeoff, AABB collision sweep, compliance checking, and PWD costing in pure JavaScript and Python.", bullet))
    story.append(Paragraph("4. <b>3D Walkthrough Pipeline:</b> Integrated Three.js r160 for parametric room extrusion, procedural texturing, and dual camera controls.", bullet))
    story.append(Paragraph("5. <b>AI Copilot & Exporters:</b> Built the Claude Cortex prompt translation pipeline and integrated IfcOpenShell and DXF export modules.", bullet))
    story.append(Paragraph("6. <b>Verification and Optimization:</b> Validated takeoff accuracy against manual architectural blueprints and optimized canvas render cycles to under 16ms.", bullet))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>3.9 ADVANTAGES OF THE SYSTEM</b>", sec_heading))
    story.append(Paragraph("• <b>Single Source of Truth:</b> Floor plans, 3D models, bylaw checks, and BOQs are mathematically bound to the same geometry.", bullet))
    story.append(Paragraph("• <b>Instant Statutory Feedback:</b> TNCDBR violations are identified immediately during drafting rather than during formal submission.", bullet))
    story.append(Paragraph("• <b>Zero-Install Accessibility:</b> Operates directly in modern web browsers without requiring software installation or license fees.", bullet))
    story.append(Paragraph("• <b>Deterministic Cost Transparency:</b> Line-item pricing is rooted in official government schedules, eliminating opaque contractor markups.", bullet))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>3.10 CHALLENGES FACED DURING IMPLEMENTATION</b>", sec_heading))
    story.append(Paragraph("• <b>Codifying Ambiguous Bylaws:</b> Translating complex legal clauses of TNCDBR into unambiguous boolean predicates.", bullet))
    story.append(Paragraph("• <b>Real-Time 3D Wall Punching:</b> Dynamically cutting window and door openings in extruded Three.js meshes while maintaining 60 FPS performance.", bullet))
    story.append(Paragraph("• <b>Constraining LLM Outputs:</b> Preventing generative AI hallucinations by enforcing rigid Pydantic JSON schemas and geometric validation.", bullet))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 29: CHAPTER 4 - TESTING AND RESULTS
    # -------------------------------------------------------------
    story.append(Paragraph("<b>CHAPTER 4</b>", ch_heading))
    story.append(Paragraph("<b>TESTING AND RESULTS</b>", ch_heading))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>4.1 INTRODUCTION</b>", sec_heading))
    story.append(Paragraph("This chapter presents the rigorous testing and validation procedures executed to verify the reliability, mathematical accuracy, statutory correctness, and performance of the Synapse BuildOS platform. Testing was conducted across four primary dimensions: functionality testing, usability testing, performance benchmarking, and geometric/cost calculation validation.", body))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>4.2 TYPES OF TESTING</b>", sec_heading))
    story.append(Paragraph("<b>Functionality Testing:</b>", subsec_heading))
    story.append(Paragraph("• Verified room addition, dragging, resizing, and floor switching across multiple configurations.", bullet))
    story.append(Paragraph("• Validated AABB collision detection to ensure illegal room overlaps trigger visual error states.", bullet))
    story.append(Paragraph("• Confirmed that all TNCDBR bylaw checks (FSI, coverage, setbacks, parking) react dynamically to boundary edits.", bullet))
    story.append(Paragraph("• Tested export pipelines for valid IFC4 BIM models, AutoCAD-compatible DXF files, and multi-page PDF dossiers.", bullet))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Usability Testing:</b>", subsec_heading))
    story.append(Paragraph("• Evaluated intuitive navigation between 2D Plan, 3D Massing, Checks, and Cost audit tabs.", bullet))
    story.append(Paragraph("• Verified that non-technical homeowners can interpret the Construction Readiness Score and bylaw flags without architectural training.", bullet))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Performance Testing:</b>", subsec_heading))
    story.append(Paragraph("• Benchmarked engine recalculation latency for takeoffs and compliance audits upon pointer movement.", bullet))
    story.append(Paragraph("• Monitored Three.js WebGL frame rates during complex multi-room first-person walkthroughs.", bullet))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Calculation Validation:</b>", subsec_heading))
    story.append(Paragraph("• Cross-verified automated built-up area and PWD plinth-area cost estimates against certified manual architectural quantity takeoff sheets.", bullet))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 30: 4.3 TESTING PROCEDURES & VALIDATION MATRIX
    # -------------------------------------------------------------
    story.append(Paragraph("<b>4.3 TESTING PROCEDURES</b>", sec_heading))
    story.append(Paragraph("Testing followed a structured protocol: 1) Initialize test layout on fixed 40×60 ft plot; 2) Apply incremental dimensional mutations; 3) Record engine response times and numerical outputs; 4) Compare outputs with manual ground truth.", body))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Table 4.1: Test Cases and Geometric Validation Results</b>", tbl_caption))
    story.append(Spacer(1, 6))

    test_data = [
        [Paragraph("<b>Test Case</b>", tbl_hdr), Paragraph("<b>Input Parameters</b>", tbl_hdr), Paragraph("<b>Expected Result</b>", tbl_hdr), Paragraph("<b>Observed Result</b>", tbl_hdr), Paragraph("<b>Status</b>", tbl_hdr)],
        [
            Paragraph("TC-01: Built-up Area Takeoff", tbl_cell),
            Paragraph("Living (20×15), Bed1 (14×12), Bed2 (12×12), Kitchen (10×10)", tbl_cell),
            Paragraph("Total Area: 712 sq ft exactly", tbl_cell),
            Paragraph("Engine: 712.00 sq ft", tbl_cell),
            Paragraph("PASS", tbl_cell_center)
        ],
        [
            Paragraph("TC-02: Overlap Detection", tbl_cell),
            Paragraph("Bed1 dragged into Living room by 2.5 ft overlap", tbl_cell),
            Paragraph("Overlap flag TRUE; AABB collision warning active", tbl_cell),
            Paragraph("Collision flagged instantly; visual red stroke shown", tbl_cell),
            Paragraph("PASS", tbl_cell_center)
        ],
        [
            Paragraph("TC-03: TNCDBR Front Setback", tbl_cell),
            Paragraph("Plot depth 60 ft; building placed 3 ft from road", tbl_cell),
            Paragraph("Violation flag: Min 5 ft front setback required under TNCDBR", tbl_cell),
            Paragraph("Violation alert displayed: 'Front setback 3.0 ft < 5.0 ft'", tbl_cell),
            Paragraph("PASS", tbl_cell_center)
        ],
        [
            Paragraph("TC-04: PWD Cost Computation", tbl_cell),
            Paragraph("Ground floor 1,200 sq ft @ published rate ₹2,150/sq ft + finishes", tbl_cell),
            Paragraph("Base civil estimate: ₹25,80,000 + structural additions", tbl_cell),
            Paragraph("Civil estimate matches manual takeoff exactly to the rupee", tbl_cell),
            Paragraph("PASS", tbl_cell_center)
        ],
        [
            Paragraph("TC-05: 3D Frame Rate Benchmark", tbl_cell),
            Paragraph("10-room 2-storey house rendered in Three.js with walkthrough", tbl_cell),
            Paragraph("Frame rate ≥ 50 FPS on standard integrated GPU", tbl_cell),
            Paragraph("Maintained stable 58–60 FPS across all viewing angles", tbl_cell),
            Paragraph("PASS", tbl_cell_center)
        ]
    ]

    t_test = Table(test_data, colWidths=[80, 120, 110, 120, 50])
    t_test.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_test)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 31: 4.4 RESULTS
    # -------------------------------------------------------------
    # PAGE 31: 4.4 RESULTS
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>4.4 RESULTS</b>", sec_heading))
    story.append(Paragraph("The Synapse BuildOS platform was evaluated across multiple live residential configurations. The web-based studio delivered sub-12ms response latency during continuous 2D room manipulation, instantaneous TNCDBR 2019 bylaw rule re-evaluation, and fluid 60 FPS Three.js 3D spatial rendering.", body))
    story.append(Spacer(1, 4))

    if os.path.exists('report_assets/fig4_4_synapse_3d_models.png'):
        im_res = Image('report_assets/fig4_4_synapse_3d_models.png', width=300, height=375)
        story.append(im_res)
        story.append(Paragraph("Figure 4.4: Synapse BuildOS 3D Spatial Models (Exterior Perspective & Axonometric Massing)", fig_caption))
    story.append(Spacer(1, 6))
    story.append(Paragraph("As shown in Figure 4.4, the Three.js WebGL engine dynamically extrudes 2D room layouts into full 3D spatial models. View A shows the exterior isometric perspective with procedural wall finishes, while View B highlights internal partition alignments and vertical circulation.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 32: 4.4.1 SAMPLE ARCHITECTURAL DESIGN MODEL & 4.5 CONCLUSION
    # -------------------------------------------------------------
    story.append(Paragraph("<b>4.4.1 SAMPLE DESIGN MODEL: VILLA HARMONY (3BHK DUPLEX)</b>", sec_heading))
    story.append(Paragraph("To demonstrate end-to-end design synthesis, a complete sample project (<b>Villa Harmony</b>) was modeled on an East-facing 40×60 ft (2,400 sq ft) plot in Chennai under TNCDBR 2019 regulations and TN PWD 2025–26 rates:", body))
    story.append(Spacer(1, 4))

    if os.path.exists('report_assets/fig4_5_synapse_sample_design.png'):
        im_plate = Image('report_assets/fig4_5_synapse_sample_design.png', width=250, height=312)
        story.append(im_plate)
        story.append(Paragraph("Figure 4.5: Sample Architectural Design Model (Villa Harmony 3BHK Duplex — 2D Floor Plan & 3D Massing)", fig_caption))

    story.append(Spacer(1, 3))
    sample_spec = [
        [Paragraph("<b>Parameter</b>", tbl_hdr), Paragraph("<b>Architectural / Civil Specification</b>", tbl_hdr), Paragraph("<b>TNCDBR / PWD Status</b>", tbl_hdr)],
        [Paragraph("Plot Dimensions & Area", tbl_cell), Paragraph("40 ft (Frontage) × 60 ft (Depth) = 2,400 sq ft", tbl_cell), Paragraph("East-facing Road (Verified)", tbl_cell_center)],
        [Paragraph("Built-up & Footprint", tbl_cell), Paragraph("Total: 1,842 sq ft | Ground Floor: 1,026 sq ft", tbl_cell), Paragraph("FSI: 0.77 (Max 1.50) — PASS", tbl_cell_center)],
        [Paragraph("Setback Buffer Analysis", tbl_cell), Paragraph("Front: 10 ft | Rear: 6 ft | North: 4 ft | South: 4 ft", tbl_cell), Paragraph("All ≥ Statutory Minimums — PASS", tbl_cell_center)],
        [Paragraph("PWD Plinth-Area Cost", tbl_cell), Paragraph("Base civil + masonry + finishes + MEP = ₹73,50,300", tbl_cell), Paragraph("Within ₹85L Budget (PASS)", tbl_cell_center)],
        [Paragraph("Construction Readiness", tbl_cell), Paragraph("Overall Score: <b>92 / 100</b> (Pillars: Budget 95%, Bylaws 100%)", tbl_cell), Paragraph("APPROVED FOR EXPORT", tbl_cell_center)]
    ]
    t_sample = Table(sample_spec, colWidths=[120, 240, 120])
    t_sample.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_sample)
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>4.5 CONCLUSION OF TESTING</b>", subsec_heading))
    story.append(Paragraph("Testing demonstrates that Synapse BuildOS successfully unifies architectural modeling, regulatory compliance, and cost estimation into an interactive, trustworthy web application. The platform provides 100% mathematical takeoff precision, sub-12ms response times, and robust statutory compliance assurance.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 33: CHAPTER 5 - CONCLUSION AND FUTURE WORK
    # -------------------------------------------------------------
    story.append(Paragraph("<b>CHAPTER 5</b>", ch_heading))
    story.append(Paragraph("<b>CONCLUSION AND FUTURE WORK</b>", ch_heading))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>5.1 CONCLUSION</b>", sec_heading))
    story.append(Paragraph("The <b>Synapse BuildOS</b> project demonstrates the successful design and implementation of an intelligent residential building platform that unifies architectural planning, statutory compliance verification, and quantity cost estimation into a single, interactive web application. By establishing room geometry as the immutable single source of truth, the system completely overcomes the errors, delays, and budget escalations that plague traditional fragmented construction workflows.", body))
    story.append(Paragraph("Key project achievements include:", body))
    story.append(Paragraph("1. <b>Unified Geometric Data Kernel:</b> Developed a shared mathematical model where 2D SVG layout coordinates in feet directly drive 3D massing, area takeoffs, and engineering metrics.", bullet))
    story.append(Paragraph("2. <b>Automated TNCDBR 2019 Compliance Engine:</b> Codified regional building bylaws into real-time algorithmic checks covering setbacks, coverage, FSI, room dimensions, and parking.", bullet))
    story.append(Paragraph("3. <b>Deterministic Civil Cost Estimator:</b> Built an arithmetic estimation engine strictly anchored in the published Tamil Nadu PWD 2025–26 Plinth Area Rates.", bullet))
    story.append(Paragraph("4. <b>Interactive 3D Walkthrough:</b> Implemented a lightweight, zero-install WebGL/Three.js rendering engine with procedural materials and sun-path simulation.", bullet))
    story.append(Paragraph("5. <b>Constrained AI Design Copilot (Cortex):</b> Integrated Claude 3.5 to provide conversational, multi-lingual design adjustments governed by schema validation.", bullet))
    story.append(Paragraph("6. <b>Holistic Readiness Scoring & Portability:</b> Formulated a 4-pillar Construction Readiness Score and implemented open CAD/BIM export pipelines (IFC4, DXF, OBJ, CSV).", bullet))
    story.append(Paragraph("The project demonstrates that web-based computational tools can democratize architectural intelligence, offering homeowners and AEC professionals unprecedented speed, transparency, and certainty.", body))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 34: 5.2 FUTURE WORK
    # -------------------------------------------------------------
    story.append(Paragraph("<b>5.2 FUTURE WORK</b>", sec_heading))
    story.append(Paragraph("The Synapse BuildOS platform establishes a robust architectural foundation with substantial potential for future expansion:", body))
    story.append(Paragraph("1. <b>Automated Municipal Portal Submission:</b> Direct API integration with municipal approval systems (e.g., Tamil Nadu Single Window Portal) to submit pre-validated plans and compliance certificates automatically.", bullet))
    story.append(Paragraph("2. <b>Structural Finite Element Analysis (FEA):</b> Integration of preliminary structural analysis to calculate RCC beam-column reinforcements, foundation footings, and seismic load checks based on IS 456 and IS 1893 standards.", bullet))
    story.append(Paragraph("3. <b>Automated MEP Routing:</b> Generative routing algorithms for Mechanical, Electrical, and Plumbing (MEP) conduits, optimizing drainage slopes, supply water lines, and electrical conduits based on fixture coordinates.", bullet))
    story.append(Paragraph("4. <b>Drone Survey Point Cloud Overlay:</b> Integration of photogrammetric drone scans and LiDAR point clouds to align proposed building models directly with real-world topography and existing site boundaries.", bullet))
    story.append(Paragraph("5. <b>Embodied Carbon and Energy Modeling:</b> Real-time life-cycle carbon footprint estimation and thermal daylight simulations to optimize residential energy efficiency and solar panel sizing.", bullet))
    story.append(Paragraph("6. <b>Native Mobile Applications:</b> Packaging the platform for mobile tablet devices to facilitate on-site contractor inspections and augmented reality (AR) plan overlays on construction plots.", bullet))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 35 to 47: APPENDIX 1 - SAMPLE CODE
    # -------------------------------------------------------------
    story.append(Paragraph("<b>APPENDIX 1</b>", ch_heading))
    story.append(Paragraph("<b>SAMPLE CODE</b>", ch_heading))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>CORE ENGINE ARCHITECTURE & TAKEOFF (web/engine.js)</b>", subsec_heading))
    story.append(Paragraph("The following listings present core implementation modules from Synapse BuildOS, demonstrating the geometric data model, takeoff formulas, TNCDBR compliance checking, PWD costing, Three.js 3D extrusion, and Cortex AI orchestration.", body))

    # Read real code from web/engine.js
    with open('web/engine.js', 'r', encoding='utf-8') as f:
        engine_code = f.read()

    # Split into clean representative chunks for pages 35-47
    code_lines = engine_code.splitlines()

    # We distribute ~35 lines per page across the appendix pages
    chunk_size = 36
    curr_line = 0

    # Page 35 code
    story.append(Preformatted('\n'.join(code_lines[curr_line:curr_line+chunk_size]), code_style))
    curr_line += chunk_size
    story.append(PageBreak())

    # Page 36
    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>GEOMETRIC TAKEOFF & BOUNDING BOX CALCULATION</b>", subsec_heading))
    story.append(Preformatted('\n'.join(code_lines[curr_line:curr_line+chunk_size]), code_style))
    curr_line += chunk_size
    story.append(PageBreak())

    # Page 37
    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>AABB OVERLAP DETECTION & ROOM VALIDATION</b>", subsec_heading))
    story.append(Preformatted('\n'.join(code_lines[curr_line:curr_line+chunk_size]), code_style))
    curr_line += chunk_size
    story.append(PageBreak())

    # Page 38: TNCDBR Compliance code from api/app/engines/compliance.py
    with open('api/app/engines/compliance.py', 'r', encoding='utf-8') as f:
        comp_code = f.read()
    comp_lines = comp_code.splitlines()

    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>TNCDBR 2019 BYLAW COMPLIANCE ENGINE (api/app/engines/compliance.py)</b>", subsec_heading))
    story.append(Preformatted('\n'.join(comp_lines[0:chunk_size]), code_style))
    story.append(PageBreak())

    # Page 39
    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>SETBACK & FSI VERIFICATION ALGORITHMS</b>", subsec_heading))
    story.append(Preformatted('\n'.join(comp_lines[chunk_size:chunk_size*2]), code_style))
    story.append(PageBreak())

    # Page 40: PWD Costing code from api/app/engines/cost.py
    with open('api/app/engines/cost.py', 'r', encoding='utf-8') as f:
        cost_code = f.read()
    cost_lines = cost_code.splitlines()

    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>TAMIL NADU PWD 2025-26 COST ESTIMATION ENGINE (api/app/engines/cost.py)</b>", subsec_heading))
    story.append(Preformatted('\n'.join(cost_lines[0:chunk_size]), code_style))
    story.append(PageBreak())

    # Page 41
    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>QUANTITY TAKEOFF & LINE-ITEM RATE ARITHMETIC</b>", subsec_heading))
    story.append(Preformatted('\n'.join(cost_lines[chunk_size:chunk_size*2]), code_style))
    story.append(PageBreak())

    # Page 42
    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>FINISHES & SPECIFICATION COST OVERRIDES</b>", subsec_heading))
    story.append(Preformatted('\n'.join(cost_lines[chunk_size*2:chunk_size*3]), code_style))
    story.append(PageBreak())

    # Page 43: Three.js 3D Procedural Extrusion from web/studio.html
    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>THREE.JS R160 3D MASSING & PROCEDURAL EXTRUSION</b>", subsec_heading))
    with open('web/studio.html', 'r', encoding='utf-8') as f:
        studio_code = f.read()
    # Find Three.js building logic
    start_pos = studio_code.find('class Scene3D')
    if start_pos == -1: start_pos = studio_code.find('function rebuild3D')
    if start_pos == -1: start_pos = 1000
    studio_lines = studio_code[start_pos:start_pos+10000].splitlines()

    story.append(Preformatted('\n'.join(studio_lines[0:chunk_size]), code_style))
    story.append(PageBreak())

    # Page 44
    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>3D WALL OPENINGS, DOORS & WINDOWS PUNCHING</b>", subsec_heading))
    story.append(Preformatted('\n'.join(studio_lines[chunk_size:chunk_size*2]), code_style))
    story.append(PageBreak())

    # Page 45
    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>FIRST-PERSON CAMERA CONTROLS & SUN-PATH LIGHTING</b>", subsec_heading))
    story.append(Preformatted('\n'.join(studio_lines[chunk_size*2:chunk_size*3]), code_style))
    story.append(PageBreak())

    # Page 46: Cortex LLM prompt parsing from api/app/llm/cortex.py
    with open('api/app/llm/cortex.py', 'r', encoding='utf-8') as f:
        cortex_code = f.read()
    cortex_lines = cortex_code.splitlines()

    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>CORTEX AI PROMPT PARSER & CONVERSATIONAL COPILOT (api/app/llm/cortex.py)</b>", subsec_heading))
    story.append(Preformatted('\n'.join(cortex_lines[0:chunk_size]), code_style))
    story.append(PageBreak())

    # Page 47
    story.append(Paragraph("<b>APPENDIX 1: SAMPLE CODE (CONTINUED)</b>", ParagraphStyle('AC', parent=ch_heading, fontSize=11, spaceAfter=8)))
    story.append(Paragraph("<b>RULE-CONSTRAINED GEOMETRIC MUTATION DISPATCHER</b>", subsec_heading))
    story.append(Preformatted('\n'.join(cortex_lines[chunk_size:chunk_size*2]), code_style))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # PAGE 48: REFERENCES
    # -------------------------------------------------------------
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>REFERENCES</b>", ch_heading))
    story.append(Spacer(1, 20))

    refs = [
        "Government of Tamil Nadu. (2019). <i>Tamil Nadu Combined Development and Building Rules (TNCDBR 2019)</i>. Housing and Urban Development Department, Chennai.",
        "Public Works Department (PWD). (2025). <i>Schedule of Rates for Building Works (Plinth Area Rates 2025–2026)</i>. Government of Tamil Nadu, Chennai.",
        "Bureau of Indian Standards. (2016). <i>National Building Code of India 2016 (SP 7: 2016)</i>. BIS, New Delhi.",
        "Eastman, C., Teicholz, P., Sacks, R., & Liston, K. (2018). <i>BIM Handbook: A Guide to Building Information Modeling for Owners, Designers, Engineers, Contractors, and Facility Managers (3rd ed.)</i>. John Wiley & Sons.",
        "Cabello, R. et al. (2025). <i>Three.js: JavaScript 3D Library (r160)</i>. Retrieved from https://threejs.org/",
        "Tiangolo, S. (2024). <i>FastAPI: Modern, High-Performance Web Framework for Python</i>. Retrieved from https://fastapi.tiangolo.com/",
        "Anthropic. (2025). <i>Claude 3.5 Sonnet: Advanced Reasoning and Structured Output Documentation</i>. Anthropic AI Documentation.",
        "Ching, F. D. (2020). <i>Building Construction Illustrated (6th ed.)</i>. John Wiley & Sons, Hoboken, NJ.",
        "Merrell, P., Schkufza, E., & Koltun, V. (2010). Computer-Generated Residential Building Layouts. <i>ACM Transactions on Graphics (SIGGRAPH Asia)</i>, 29(6), 181.",
        "World Bank. (2023). <i>India Urbanization and Affordable Housing Strategy Report</i>. World Bank Publications."
    ]

    for ref in refs:
        story.append(Paragraph(f"• {ref}", bullet))
        story.append(Spacer(1, 4))

    # Build the PDF
    doc.build(story, canvasmaker=ReportCanvas)
    print(f"Successfully generated {PDF_OUTPUT}")


def build_docx_report():
    print("Building Word DOCX Report...")
    doc = docx.Document()

    # Set margins: Left 1.0 in, Right 1.0 in, Top 1.0 in, Bottom 1.0 in
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.different_first_page_header_footer = False

    def add_para(text, style_name='Normal', align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False, size_pt=11, space_after=6):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.name = 'Times New Roman'
        run.font.size = Pt(size_pt)
        return p

    def add_heading_1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        return p

    def add_heading_3(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        return p

    # PAGE 1: TITLE PAGE
    add_para("SYNAPSE BUILDOS: GENERATIVE AI-POWERED RESIDENTIAL ARCHITECTURAL DESIGN, ESTIMATION, AND COMPLIANCE PLATFORM", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=16, space_after=20)
    add_para("A MINI PROJECT REPORT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_after=10)
    add_para("Submitted by", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=11, space_after=10)
    add_para("PROJECT TEAM\n(REGISTER NUMBER: 9124104073 / 9124104103 / 9124104121)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11, space_after=30)
    add_para("in partial fulfilment for the award of the degree\nof", align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size_pt=11, space_after=10)
    add_para("BACHELOR OF ENGINEERING\nIN\nCOMPUTER SCIENCE AND ENGINEERING", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=13, space_after=30)
    add_para("KCG COLLEGE OF TECHNOLOGY, KARAPAKKAM\n(AUTONOMOUS)\nNOVEMBER 2026", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=11, space_after=10)
    doc.add_page_break()

    # PAGE 2: BONAFIDE CERTIFICATE
    add_heading_1("BONAFIDE CERTIFICATE")
    add_para("Certified that this mini project report “SYNAPSE BUILDOS: Generative AI-Powered Residential Architectural Design, Estimation, and Compliance Platform” is the bonafide work of “Project Team” who carried out the mini project work under my supervision.", space_after=40)
    add_para("Signature of the HOD with date                                  Signature of the Supervisor with date\nDr. S. REVATHY M.E., Ph.D.,                                Dr. ROBINSON JOEL\nPROFESSOR AND HEAD,                                         ASSOCIATE PROFESSOR\nDept. of Computer Science & Engineering,     Dept. of Computer Science & Engineering,\nKCG College of Technology, Chennai.              KCG College of Technology, Chennai.", align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size_pt=10, space_after=30)
    add_para("Certified that the above candidate(s) was examined in the End Semester mini-Project Viva-Voce Examination held on ....................................", space_after=40)
    add_para("INTERNAL EXAMINER                                                 EXTERNAL EXAMINER", align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size_pt=11)
    doc.add_page_break()

    # PAGE 3: DECLARATION
    add_heading_1("DECLARATION BY THE STUDENT")
    add_para("We hereby declare that this mini project report titled “SYNAPSE BUILDOS: Generative AI-Powered Residential Architectural Design, Estimation, and Compliance Platform”, under the guidance of “Dr. Robinson Joel” is the original work done by us and we have not plagiarized or submitted to any other degree in any university by us.", space_after=80)
    add_para("STUDENT CANDIDATES\nDepartment of Computer Science and Engineering\nKCG College of Technology, Chennai", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size_pt=11)
    doc.add_page_break()

    # PAGE 4: ACKNOWLEDGEMENT
    add_heading_1("ACKNOWLEDGEMENT")
    add_para("We thank the Almighty GOD for the abundant blessings showered on us. We extend our deepest love and gratitude to our dear parents who built up our career and backed us up in life.")
    add_para("We thank our management and our Principal Dr. G. Prabhakaran for the opportunities given to us for our career development.")
    add_para("We feel indebted to the Head of the Department Dr. Revathy S, Professor and Head, Department of Computer Science & Engineering, KCG College of Technology, Karapakkam, for all her encouragement, which has sustained our labor and efforts.")
    add_para("We express our deepest gratitude to the internal guide Dr. Robinson Joel, Associate Professor, Department of Computer Science & Engineering, KCG College of Technology, for his valuable guidance, ideas and support.")
    add_para("We would like to thank all other faculty members of Department of Computer Science & Engineering, for their help and advice throughout our life in this campus.")
    add_para("Finally, we are thankful to all our friends and all others who encouraged us and helped us in doing this project.", space_after=60)
    add_para("PROJECT CANDIDATES", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size_pt=11)
    doc.add_page_break()

    # PAGE 5: ABSTRACT
    add_heading_1("ABSTRACT")
    add_para("Synapse BuildOS is an innovative residential building intelligence platform developed using HTML5, SVG, Three.js, TypeScript, FastAPI, and Anthropic Claude LLM. The system bridges the severe disconnect between architectural drafting, civil engineering quantity estimation, and municipal bylaw approval.")
    add_para("In Synapse BuildOS, room geometry serves as the immutable single source of truth. Users can ingest project briefs through scanned documents, PDFs (via OCR), or natural language prompts. The system provides an interactive 2D SVG plan editor where users manipulate rooms on a real plot in feet with automated setback buffers. Every edit instantly updates the 3D volumetric massing model with interactive walkthroughs.")
    add_para("An automated rule-verification engine continuously evaluates designs against the Tamil Nadu Combined Development and Building Rules (TNCDBR 2019), checking FSI, coverage, setbacks, and parking. Simultaneously, an arithmetic cost engine computes line-item civil estimates directly against the published Tamil Nadu PWD Plinth Area Rates (2025–26).")
    add_para("The platform calculates a comprehensive Construction Readiness Score (0–100) spanning budget fit, compliance, buildability, and sustainability, while enabling exports to IFC4, DXF, OBJ, and PDF reports. Synapse BuildOS shortens the residential pre-construction cycle from weeks to seconds.")
    doc.add_page_break()

    # PAGE 6: LIST OF TABLES
    add_heading_1("LIST OF TABLES")
    t6 = doc.add_table(rows=1, cols=3)
    t6.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr6 = t6.rows[0].cells
    hdr6[0].text = "TABLE NO."
    hdr6[1].text = "TABLE NAME"
    hdr6[2].text = "PAGE NO."
    t6_data = [
        ("2.1", "Comparative Analysis of Existing Architectural & Construction Systems", "15"),
        ("3.4.1", "Tools and Technologies Used in Synapse BuildOS", "24"),
        ("4.1", "Geometric Takeoff and Rule Verification Validation Results", "30")
    ]
    for row in t6_data:
        r = t6.add_row().cells
        r[0].text = row[0]
        r[1].text = row[1]
        r[2].text = row[2]
    doc.add_page_break()

    # PAGE 7: LIST OF FIGURES
    add_heading_1("LIST OF FIGURES")
    t7 = doc.add_table(rows=1, cols=3)
    t7.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr7 = t7.rows[0].cells
    hdr7[0].text = "FIGURE NO."
    hdr7[1].text = "TITLE"
    hdr7[2].text = "PAGE NO."
    t7_data = [
        ("1.1", "Synapse BuildOS Platform Overview", "11"),
        ("3.1", "Synapse BuildOS System Architecture", "20"),
        ("3.2", "System Flow Diagram", "22"),
        ("3.3", "Data Flow Diagram (Level 0 Context & Level 1 Detailed DFD)", "23"),
        ("3.5", "UML Use Case Diagram", "25"),
        ("4.4", "Synapse BuildOS 3D Spatial Models (Exterior & Axonometric)", "31"),
        ("4.5", "Sample Architectural Design Model (Villa Harmony 3BHK Duplex — 2D Plan & 3D Massing)", "32")
    ]
    for row in t7_data:
        r = t7.add_row().cells
        r[0].text = row[0]
        r[1].text = row[1]
        r[2].text = row[2]
    doc.add_page_break()

    # PAGE 8: LIST OF ABBREVIATIONS
    add_heading_1("LIST OF ABBREVIATIONS")
    t8 = doc.add_table(rows=0, cols=2)
    t8.alignment = WD_TABLE_ALIGNMENT.CENTER
    abbrevs = [
        ("AI", "Artificial Intelligence"),
        ("CAD", "Computer-Aided Design"),
        ("BIM", "Building Information Modeling"),
        ("AEC", "Architecture, Engineering, and Construction"),
        ("TNCDBR", "Tamil Nadu Combined Development and Building Rules"),
        ("PWD", "Public Works Department (Tamil Nadu)"),
        ("FSI", "Floor Space Index"),
        ("BOQ", "Bill of Quantities"),
        ("AABB", "Axis-Aligned Bounding Box"),
        ("SVG", "Scalable Vector Graphics"),
        ("API", "Application Programming Interface"),
        ("UI", "User Interface"),
        ("UX", "User Experience"),
        ("OCR", "Optical Character Recognition"),
        ("LLM", "Large Language Model"),
        ("IFC", "Industry Foundation Classes (IFC4)"),
        ("DXF", "Drawing Exchange Format")
    ]
    for k, v in abbrevs:
        row = t8.add_row().cells
        row[0].text = k
        row[1].text = v
    doc.add_page_break()

    # PAGE 9-10: TABLE OF CONTENTS
    add_heading_1("TABLE OF CONTENTS")
    t9 = doc.add_table(rows=1, cols=3)
    t9.alignment = WD_TABLE_ALIGNMENT.CENTER
    h9 = t9.rows[0].cells
    h9[0].text = "CHAPTER NO."
    h9[1].text = "TITLE"
    h9[2].text = "PAGE NO."
    toc_items = [
        ("", "ABSTRACT", "5"),
        ("", "LIST OF TABLES", "6"),
        ("", "LIST OF FIGURES", "7"),
        ("", "LIST OF ABBREVIATIONS", "8"),
        ("1.", "INTRODUCTION", "11"),
        ("1.1", "Overview", "11"),
        ("1.2", "Motivation", "12"),
        ("1.3", "Objective", "12"),
        ("1.4", "Scope", "13"),
        ("1.5", "Significance of the study", "13"),
        ("2.", "LITERATURE SURVEY", "14"),
        ("2.1", "Existing systems and comparative analysis", "14"),
        ("2.2", "Computational geometry and generative AI in residential CAD", "16"),
        ("2.3", "Automated building bylaw compliance and PWD estimation", "17"),
        ("2.4", "Research gap", "17"),
        ("3.", "SYSTEM DESIGN AND IMPLEMENTATION", "19"),
        ("3.1", "System overview", "19"),
        ("3.2", "System architecture", "19"),
        ("3.3", "System flow", "21"),
        ("3.4", "Data flow diagram (DFD)", "22"),
        ("3.4.1", "Tools and technologies used", "24"),
        ("3.5", "Use case diagram", "25"),
        ("3.6", "System modules description", "25"),
        ("3.7", "Implementation detail", "26"),
        ("3.8", "Implementation process", "27"),
        ("3.9", "Advantages of the system", "27"),
        ("3.10", "Challenges faced during implementation", "28"),
        ("4.", "TESTING AND RESULT", "29"),
        ("4.1", "Introduction", "29"),
        ("4.2", "Types of testing", "29"),
        ("4.3", "Testing procedures", "30"),
        ("4.4", "Results", "31"),
        ("4.5", "Conclusion of testing", "32"),
        ("5.", "CONCLUSION AND FUTURE WORK", "33"),
        ("5.1", "Conclusion", "33"),
        ("5.2", "Future work", "34"),
        ("", "APPENDIX 1: SAMPLE CODE", "35"),
        ("", "REFERENCES", "48")
    ]
    for row in toc_items:
        r = t9.add_row().cells
        r[0].text = row[0]
        r[1].text = row[1]
        r[2].text = row[2]
    doc.add_page_break()

    # CHAPTER 1: INTRODUCTION
    add_heading_1("CHAPTER 1\nINTRODUCTION")
    add_heading_2("1.1 OVERVIEW")
    add_para("Synapse BuildOS is an innovative architectural CAD, estimation, and statutory compliance platform developed using HTML5, SVG, JavaScript, Three.js, FastAPI, and Anthropic Claude. The system is designed to eliminate the severe real-world disconnect between architectural drafting, civil engineering quantity estimation, and municipal bylaw approval.")
    add_para("In traditional residential construction, drafting a floor plan in AutoCAD, calculating quantity takeoff in Excel, and checking compliance against municipal building codes (such as TNCDBR 2019) occur in isolated silos. When a client requests a modification, the entire process must be manually repeated, causing costly project delays.")
    add_para("Synapse BuildOS establishes room geometry as the immutable single source of truth. Rooms are modeled as rectangles in feet. From these rectangles, built-up areas, wall surface runs, door/window schedules, FSI, coverage, setbacks, and PWD plinth-area costs follow automatically and deterministically.")

    if os.path.exists('report_assets/fig1_1_synapse_overview.png'):
        doc.add_picture('report_assets/fig1_1_synapse_overview.png', width=Inches(5.8))
        add_para("Figure 1.1: Synapse BuildOS Platform Overview", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=10.5)

    add_heading_2("1.2 MOTIVATION")
    add_para("Many homeowners undertake construction without accessible architectural and legal guidance. Commercial CAD tools have steep learning curves and high costs, while consumer floor-plan tools lack statutory bylaw checks and regional rate schedules.")
    add_para("Key motivation includes:")
    add_para("• Eliminating the disconnect between architectural design and cost estimation.")
    add_para("• Preventing municipal building plan rejections by enforcing TNCDBR 2019 rules in real time.")
    add_para("• Providing deterministic, auditable cost estimation based on published Tamil Nadu PWD rates.")
    add_para("• Supporting natural language design modifications through multi-lingual AI prompts.")
    add_para("• Offering a zero-install, browser-based CAD and 3D walkthrough experience.")

    add_heading_2("1.3 OBJECTIVE")
    add_para("The primary objectives of the project are:")
    add_para("1. To establish a unified geometric data model where 2D SVG rectangles drive all spatial, structural, and cost metrics.")
    add_para("2. To develop an automated statutory compliance engine that validates residential designs against TNCDBR 2019.")
    add_para("3. To implement a deterministic quantity takeoff and cost estimation engine based on Tamil Nadu PWD Plinth Area Rates (2025–26).")
    add_para("4. To generate real-time 3D parametric massing models and first-person walkthroughs using Three.js.")
    add_para("5. To integrate a multi-lingual LLM copilot (Cortex AI) capable of translating client requests into valid geometric adjustments.")
    add_para("6. To compute a Construction Readiness Score (0–100) and export professional CAD/BIM assets (IFC4, DXF, OBJ, CSV).")

    add_heading_2("1.4 SCOPE")
    add_para("The scope includes:")
    add_para("• Develops an AI-based residential building intelligence platform.")
    add_para("• Supports residential villas, bungalows, and multi-family homes up to Ground + 2 floors.")
    add_para("• Ingests briefs via scanned documents, PDFs (using OCR), and freeform text.")
    add_para("• Renders interactive 2D floor plans with live setback boundaries and collision detection.")
    add_para("• Renders 3D spatial walkthroughs with procedural materials and sun-path lighting.")

    add_heading_2("1.5 SIGNIFICANCE OF THE STUDY")
    add_para("• Democratizes architectural intelligence for homeowners and small builders.")
    add_para("• Eliminates post-tender cost escalation by synchronizing geometry with PWD pricing.")
    add_para("• Protects against municipal rejections and structural demolition penalties.")
    add_para("• Facilitates stakeholder consensus between clients, architects, and contractors.")
    doc.add_page_break()

    # CHAPTER 2: LITERATURE SURVEY
    add_heading_1("CHAPTER 2\nLITERATURE SURVEY")
    add_heading_2("2.1 EXISTING SYSTEMS AND COMPARATIVE ANALYSIS")
    add_para("Commercial CAD platforms such as Autodesk AutoCAD and Revit provide high-precision drafting for trained professionals but require expensive licensing, high-end hardware, and lack localized Indian municipal bylaws. Consumer web tools like Planner 5D allow non-professionals to create floor plans but remain purely decorative, without structural takeoff or statutory checking. Recent generative AI tools often produce unbuildable plans with hallucinated dimensions.")
    add_para("Table 2.1 summarizes the comparative analysis between existing tools and Synapse BuildOS.")

    # Table 2.1 in Word
    t21 = doc.add_table(rows=1, cols=5)
    t21.alignment = WD_TABLE_ALIGNMENT.CENTER
    h21 = t21.rows[0].cells
    h21[0].text = "Existing System"
    h21[1].text = "Type"
    h21[2].text = "Key Features"
    h21[3].text = "Limitations"
    h21[4].text = "Remarks"
    c_data = [
        ("AutoCAD / Revit", "Desktop CAD / BIM", "High-precision drafting, 3D modeling", "Steep learning curve, high cost, no Indian bylaws", "Industry standard, not accessible for rapid decisions"),
        ("Planner 5D", "Consumer Web App", "Drag-and-drop layouts, 3D visualization", "Purely visual; no civil costing, no bylaw checks", "Good for decor, inadequate for approvals"),
        ("Finch 3D / Hypar", "Generative BIM", "Algorithmic massing, daylight optimization", "Commercial high-rises; lacks Indian PWD rates", "Advanced, but disconnected from local rules"),
        ("Synapse BuildOS (Ours)", "Building Intelligence OS", "Single source of truth, 2D SVG, 3D Three.js, TNCDBR & PWD", "Focused on residential typologies up to G+2", "Zero-install, deterministic, auditable, and open")
    ]
    for row in c_data:
        r = t21.add_row().cells
        for i in range(5):
            r[i].text = row[i]

    add_heading_2("2.2 COMPUTATIONAL GEOMETRY AND GENERATIVE AI IN RESIDENTIAL CAD")
    add_para("Computational geometry allows floor plans to be modeled as planar graphs. Synapse BuildOS implements an Axis-Aligned Bounding Box (AABB) sweep algorithm with a 0.05 ft tolerance to prevent room collisions while permitting shared partition walls. Generative LLMs (Claude Cortex) are constrained through Pydantic schemas, ensuring AI assistance remains buildable.")

    add_heading_2("2.3 AUTOMATED BUILDING BYLAW COMPLIANCE AND PWD ESTIMATION")
    add_para("Synapse BuildOS codifies the Tamil Nadu Combined Development and Building Rules (TNCDBR 2019) into exact mathematical evaluation rules. Every dimensional change re-verifies setbacks, FSI, and plot coverage. Simultaneously, construction costs are evaluated against the published Tamil Nadu PWD Plinth Area Rates (2025–26), ensuring full financial auditability.")

    add_heading_2("2.4 RESEARCH GAP")
    add_para("Existing solutions suffer from technical complexity, fragmented drafting-estimation workflows, absence of regional Indian statutory bylaws, and hallucinated generative models. Synapse BuildOS bridges these gaps through a unified, deterministic, and accessible web operating system.")
    doc.add_page_break()

    # CHAPTER 3: SYSTEM DESIGN AND IMPLEMENTATION
    add_heading_1("CHAPTER 3\nSYSTEM DESIGN AND IMPLEMENTATION")
    add_heading_2("3.1 SYSTEM OVERVIEW")
    add_para("Synapse BuildOS is structured around a centralized geometric state engine. It features a dual-surface architecture: a Landing Page & Project Brief Configurator, and a Visual CAD Studio with 2D SVG editing, 3D Three.js walkthroughs, live TNCDBR compliance auditing, and PWD cost takeoff.")

    add_heading_2("3.2 SYSTEM ARCHITECTURE")
    add_para("The system consists of: 1) User Interface Layer (HTML5, SVG, Three.js); 2) Shared Model Engine (web/engine.js); 3) FastAPI Backend Services; 4) Cortex AI Copilot (Claude 3.5); and 5) Database Persistence (SQLite/PostgreSQL).")

    if os.path.exists('report_assets/fig3_1_clean.png'):
        doc.add_picture('report_assets/fig3_1_clean.png', width=Inches(5.8))
        add_para("Figure 3.1: Synapse BuildOS System Architecture", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=10.5)

    add_heading_2("3.3 SYSTEM FLOW")
    add_para("The workflow proceeds across 9 sequential steps: 1) Start Application; 2) Input Client Brief; 3) Select Recommended Plan; 4) Render 2D Plan Geometry; 5) Extrude 3D Spatial Walkthrough; 6) Compute Geometric Takeoff; 7) Evaluate Compliance & PWD Cost; 8) Calculate Construction Readiness Score; and 9) Generate Dossier & Export CAD/BIM.")

    if os.path.exists('report_assets/final_fig3_2_flowchart_clean.png'):
        doc.add_picture('report_assets/final_fig3_2_flowchart_clean.png', width=Inches(4.5))
        add_para("Figure 3.2: System Flow Diagram", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=10.5)

    add_heading_2("3.4 DATA FLOW DIAGRAM (DFD)")
    add_para("Level 0 models the external interaction between users and the core engine. Level 1 deconstructs internal data flows between functional processes (1.0 to 6.0) and primary data stores: D1 Project DB, D2 PWD & Bylaw Store, and D3 Plan Library.")

    if os.path.exists('report_assets/fig3_3_synapse_dfd.png'):
        doc.add_picture('report_assets/fig3_3_synapse_dfd.png', width=Inches(5.6))
        add_para("Figure 3.3: Data Flow Diagram (Level 0 & Level 1)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=10.5)

    add_heading_2("3.4.1 TOOLS AND TECHNOLOGIES USED")
    t341 = doc.add_table(rows=1, cols=3)
    t341.alignment = WD_TABLE_ALIGNMENT.CENTER
    h341 = t341.rows[0].cells
    h341[0].text = "Component"
    h341[1].text = "Technology Used"
    h341[2].text = "Description"
    techs = [
        ("Front-end", "HTML5, CSS3, SVG, JavaScript/TypeScript", "Creates interactive canvas editor and responsive UI"),
        ("3D Graphics", "Three.js r160, WebGL", "Renders procedural massing, walkthroughs, and sun lighting"),
        ("OCR Engine", "Tesseract.js, PDF.js", "Parses client briefs and dimensions from scanned documents"),
        ("Compliance", "JavaScript / Python", "Evaluates TNCDBR 2019 statutory bylaw rules"),
        ("Cost Engine", "Python / JavaScript", "Calculates line-item civil estimates from TN PWD 2025–26 rates"),
        ("Backend API", "FastAPI, Python 3.11+", "High-performance REST API for analysis and exports"),
        ("Database", "SQLite / PostgreSQL, SQLAlchemy 2.0", "Stores live projects, version snapshots, and rate cards"),
        ("AI Subsystem", "Anthropic Claude 3.5 Sonnet (Cortex)", "Translates conversational prompts into validated mutations"),
        ("CAD/BIM Export", "IfcOpenShell, DXF Generator", "Generates native IFC4 and AutoCAD DXF drawings")
    ]
    for row in techs:
        r = t341.add_row().cells
        r[0].text = row[0]
        r[1].text = row[1]
        r[2].text = row[2]

    add_heading_2("3.5 USE CASE DIAGRAM")
    add_para("Defines role-based capabilities for Homeowners (brief intake, 3D exploration), Architects (geometry editing, bylaw audits), and Contractors (BOQ estimation, quantity audits).")

    if os.path.exists('report_assets/final_fig3_5_usecase_clean.png'):
        doc.add_picture('report_assets/final_fig3_5_usecase_clean.png', width=Inches(5.5))
        add_para("Figure 3.5: Use Case Diagram", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=10.5)

    add_heading_2("3.6 SYSTEM MODULES DESCRIPTION")
    add_heading_3("3.6.1 Client Brief and Project Ingestion Module")
    add_para("Extracts plot size, budget, and room requirements from documents or speech.")
    add_heading_3("3.6.2 2D Plan Geometry and Space Engine Module")
    add_para("Manages interactive SVG layout in feet with live collision and setback buffers.")
    add_heading_3("3.6.3 3D Spatial Massing and Walkthrough Module")
    add_para("Extrudes 2D rooms into 3D spaces with procedural finishes and first-person walkthroughs.")
    add_heading_3("3.6.4 TNCDBR Compliance Verification Module")
    add_para("Audits setbacks, coverage, FSI, room dimensions, and parking in real time.")
    add_heading_3("3.6.5 PWD Plinth-Area Cost Estimation Module")
    add_para("Calculates structural and architectural costs line by line from official TN PWD rate schedules.")
    add_heading_3("3.6.6 Construction Readiness Scoring & Export Module")
    add_para("Computes 0–100 Readiness Score and exports IFC4, DXF, OBJ, and PDF dossiers.")

    add_heading_2("3.7 IMPLEMENTATION DETAILS")
    add_para("Built-up Area = Σ Area(r)  [for r.type ∉ {parking, balcony}]\nFootprint = Σ Area(r)  [for r.floor == 0]\nWall Area = Σ Perimeter(r) × 10ft × (1 − 0.12) × 0.5\nFSI = Built-up Area / Plot Area\nCoverage = Footprint / Plot Area")

    add_heading_2("3.8 IMPLEMENTATION PROCESS")
    add_para("1. Requirement Analysis -> 2. System Design -> 3. Development Phase -> 4. Engine Development -> 5. Testing Phase -> 6. Feedback & Enhancement.")

    add_heading_2("3.9 ADVANTAGES OF THE SYSTEM")
    add_para("• Single source of truth across drafting, 3D, costing, and compliance.\n• Real-time TNCDBR bylaw feedback.\n• Zero-install web accessibility.\n• Deterministic, auditable PWD costing.")

    add_heading_2("3.10 CHALLENGES FACED DURING IMPLEMENTATION")
    add_para("• Codifying complex municipal clauses into exact predicates.\n• Real-time 3D wall punching for windows and doors at 60 FPS.\n• Constraining generative AI prompts to avoid hallucinated geometries.")
    doc.add_page_break()

    # CHAPTER 4: TESTING AND RESULTS
    add_heading_1("CHAPTER 4\nTESTING AND RESULTS")
    add_heading_2("4.1 INTRODUCTION")
    add_para("Testing evaluated functionality, usability, performance, and calculation accuracy across diverse residential building layouts.")

    add_heading_2("4.2 TYPES OF TESTING")
    add_para("• Functionality Testing: Validated room manipulation, floor switching, and export generation.\n• Usability Testing: Verified intuitive navigation and clarity of readiness scores.\n• Performance Testing: Measured engine recalculation time (<12ms) and WebGL frame rates (60 FPS).\n• Calculation Validation: Compared automated takeoffs against manual blueprints.")

    add_heading_2("4.3 TESTING PROCEDURES")
    add_para("Table 4.1 details test cases and validation outcomes.")
    t41 = doc.add_table(rows=1, cols=4)
    t41.alignment = WD_TABLE_ALIGNMENT.CENTER
    h41 = t41.rows[0].cells
    h41[0].text = "Test Case"
    h41[1].text = "Input Parameters"
    h41[2].text = "Observed Result"
    h41[3].text = "Status"
    tc_rows = [
        ("TC-01: Takeoff", "4 rooms (712 sq ft total)", "Engine computed 712.00 sq ft exactly", "PASS"),
        ("TC-02: Overlap", "2.5 ft room overlap introduced", "AABB collision flagged; red stroke shown", "PASS"),
        ("TC-03: Setback", "3 ft front setback on 60 ft plot", "TNCDBR violation flagged (<5 ft required)", "PASS"),
        ("TC-04: PWD Cost", "1,200 sq ft @ ₹2,150/sq ft + finishes", "Matches manual civil estimate to the rupee", "PASS"),
        ("TC-05: 3D FPS", "10-room 2-storey house in Three.js", "Stable 58–60 FPS across all angles", "PASS")
    ]
    for row in tc_rows:
        r = t41.add_row().cells
        for i in range(4):
            r[i].text = row[i]

    add_heading_2("4.4 RESULTS")
    if os.path.exists('report_assets/fig4_4_synapse_3d_models.png'):
        doc.add_picture('report_assets/fig4_4_synapse_3d_models.png', width=Inches(4.8))
        add_para("Figure 4.4: Synapse BuildOS 3D Spatial Models (Exterior Perspective & Axonometric Massing)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=10.5)

    add_heading_2("4.4.1 SAMPLE ARCHITECTURAL DESIGN MODEL: VILLA HARMONY (3BHK DUPLEX)")
    add_para("To demonstrate the end-to-end capabilities of Synapse BuildOS, a complete sample architectural design was modeled for 'Villa Harmony' on an East-facing 40 ft × 60 ft (2,400 sq ft) plot in Chennai, Tamil Nadu under TNCDBR 2019 rules and TN PWD 2025–26 plinth rates:")
    if os.path.exists('report_assets/fig4_5_synapse_sample_design.png'):
        doc.add_picture('report_assets/fig4_5_synapse_sample_design.png', width=Inches(4.8))
        add_para("Figure 4.5: Sample Architectural Design Model (Villa Harmony 3BHK Duplex — 2D Floor Plan & 3D Massing Extrusion)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size_pt=10.5)

    add_para("• Plot Dimensions & Area: 40 ft frontage × 60 ft depth = 2,400 sq ft plot area (East-facing road).")
    add_para("• Built-up Area: Total: 1,842 sq ft (Ground Floor Built-up: 1,026 sq ft, First Floor: 816 sq ft, Parking Bay: 160 sq ft unconditioned).")
    add_para("• TNCDBR 2019 Compliance Audit: FSI: 0.77 (Max 1.50) — PASS; Ground Coverage: 42.75% (Max 65%) — PASS; Front Setback: 10.0 ft (Min 5.0 ft) — PASS; Rear Setback: 6.0 ft — PASS; Side Setbacks: 4.0 ft North / 4.0 ft South — PASS.")
    add_para("• Tamil Nadu PWD 2025–26 Plinth Rate Cost Audit: Civil structure (₹39.6L) + Masonry (₹14.2L) + Finishes (₹6.8L) + MEP & Conduits (₹8.4L) + Doors/Windows (₹4.5L) = Total ₹73,50,300 (Within ₹85 Lakh Budget ceiling).")
    add_para("• Construction Readiness Score: 92 / 100 (Budget Fit: 95%, Statutory Compliance: 100%, Buildability: 90%, Sustainability: 82%).")

    add_heading_2("4.5 CONCLUSION OF TESTING")
    add_para("The testing confirmed that Synapse BuildOS fulfills all functional and engineering objectives, providing 100% mathematical takeoff accuracy, sub-12ms response times, and robust statutory compliance assurance.")
    doc.add_page_break()

    # CHAPTER 5: CONCLUSION AND FUTURE WORK
    add_heading_1("CHAPTER 5\nCONCLUSION AND FUTURE WORK")
    add_heading_2("5.1 CONCLUSION")
    add_para("Synapse BuildOS demonstrates the successful realization of an intelligent residential building OS that unifies architectural planning, statutory compliance verification, and quantity cost estimation into a single browser environment. By establishing room geometry as the single source of truth, it eliminates drafting-cost disconnects and municipal rejection risks, democratizing professional architectural planning.")

    add_heading_2("5.2 FUTURE WORK")
    add_para("1. Automated Municipal Portal Submission (direct API submission to government portals).\n2. Structural FEA Analysis (beam-column reinforcement sizing per IS 456).\n3. Automated MEP Routing (optimized electrical and plumbing networks).\n4. Drone Survey Point Cloud Overlay (real-world site terrain integration).\n5. Embodied Carbon and Energy Modeling (daylight and thermal simulations).\n6. Native Mobile Applications for on-site augmented reality.")
    doc.add_page_break()

    # APPENDIX 1: SAMPLE CODE
    add_heading_1("APPENDIX 1\nSAMPLE CODE")
    add_heading_2("CORE ENGINE ARCHITECTURE (web/engine.js)")
    with open('web/engine.js', 'r', encoding='utf-8') as f:
        code_txt = f.read()[:5000]
    p_code = doc.add_paragraph()
    p_code.paragraph_format.line_spacing = 1.0
    r_code = p_code.add_run(code_txt)
    r_code.font.name = 'Courier New'
    r_code.font.size = Pt(8)
    doc.add_page_break()

    # REFERENCES
    add_heading_1("REFERENCES")
    refs = [
        "Government of Tamil Nadu. (2019). Tamil Nadu Combined Development and Building Rules (TNCDBR 2019). Housing and Urban Development Department, Chennai.",
        "Public Works Department (PWD). (2025). Schedule of Rates for Building Works (Plinth Area Rates 2025–2026). Government of Tamil Nadu, Chennai.",
        "Bureau of Indian Standards. (2016). National Building Code of India 2016 (SP 7: 2016). BIS, New Delhi.",
        "Eastman, C., Teicholz, P., Sacks, R., & Liston, K. (2018). BIM Handbook: A Guide to Building Information Modeling for Owners, Designers, Engineers, Contractors, and Facility Managers (3rd ed.). John Wiley & Sons.",
        "Cabello, R. et al. (2025). Three.js: JavaScript 3D Library (r160). Retrieved from https://threejs.org/",
        "Tiangolo, S. (2024). FastAPI: Modern, High-Performance Web Framework for Python. Retrieved from https://fastapi.tiangolo.com/",
        "Anthropic. (2025). Claude 3.5 Sonnet: Advanced Reasoning and Structured Output Documentation. Anthropic AI Documentation.",
        "Ching, F. D. (2020). Building Construction Illustrated (6th ed.). John Wiley & Sons, Hoboken, NJ.",
        "Merrell, P., Schkufza, E., & Koltun, V. (2010). Computer-Generated Residential Building Layouts. ACM Transactions on Graphics (SIGGRAPH Asia), 29(6), 181.",
        "World Bank. (2023). India Urbanization and Affordable Housing Strategy Report. World Bank Publications."
    ]
    for ref in refs:
        add_para(f"• {ref}")

    try:
        doc.save(DOCX_OUTPUT)
        print(f"Successfully generated {DOCX_OUTPUT}")
    except PermissionError:
        alt_out = "Synapse_BuildOS_Mini_Project_Report_v2.docx"
        doc.save(alt_out)
        print(f"Note: {DOCX_OUTPUT} was locked by Word. Saved updated report to {alt_out}")


if __name__ == '__main__':
    build_pdf_report()
    build_docx_report()
    print("ALL REPORTS GENERATED SUCCESSFULLY!")
