#!/usr/bin/env python3
"""
Growixa Pitch & VC Deck PDF Generator
Generates:
1. Growixa_Product_Pitch_and_GTM_Playbook.pdf (Portrait Multi-Page Guide)
2. Growixa_Investor_VC_Pitch_Deck.pdf (Landscape 16:9 Slide Deck)
"""

import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PRIMARY = colors.HexColor("#1E1B4B")      # Deep Indigo / Navy
SECONDARY = colors.HexColor("#4F46E5")    # Electric Indigo
ACCENT = colors.HexColor("#06B6D4")       # Cyan / Aqua
SUCCESS = colors.HexColor("#10B981")      # Emerald Green
BG_LIGHT = colors.HexColor("#F8FAFC")     # Light Slate Background
CARD_BG = colors.HexColor("#EEF2FF")      # Light Indigo Card
TEXT_MAIN = colors.HexColor("#0F172A")    # Dark Slate Main Text
TEXT_MUTED = colors.HexColor("#64748B")   # Slate Grey
BORDER_COLOR = colors.HexColor("#CBD5E1") # Border Grey

class NumberedCanvas(canvas.Canvas):
    """Canvas for multi-page portrait documents with headers & footers"""
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

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Top banner line
        self.setStrokeColor(SECONDARY)
        self.setLineWidth(2)
        self.line(40, 755, 572, 755)

        # Header Text
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawString(40, 762, "GROWIXA | PRODUCT PITCH & GO-TO-MARKET PLAYBOOK")

        # Footer line
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.75)
        self.line(40, 42, 572, 42)

        # Footer Text
        self.setFont("Helvetica", 8)
        self.drawString(40, 30, "Confidential - For Internal, Partner & Customer Use")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_str)
        self.restoreState()


class SlideCanvas(canvas.Canvas):
    """Canvas for landscape slides"""
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
            self.draw_slide_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_slide_decorations(self, page_count):
        self.saveState()
        # Slide Header bar
        self.setFillColor(PRIMARY)
        self.rect(0, 580, 792, 32, fill=True, stroke=False)
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 10)
        self.drawString(30, 592, "GROWIXA — INVESTOR PITCH DECK")
        self.drawRightString(762, 592, "SEED ROUND")

        # Slide Footer bar
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.75)
        self.line(30, 35, 762, 35)

        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawString(30, 22, "Growixa Inc. • The AI-Powered Growth & Campaign Automation Platform")
        page_str = f"Slide {self._pageNumber} of {page_count}"
        self.drawRightString(762, 22, page_str)
        self.restoreState()


def build_playbook_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=55,
        bottomMargin=55
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceAfter=15
    )
    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_MAIN,
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_MAIN,
        leftIndent=15,
        spaceAfter=4
    )
    callout_style = ParagraphStyle(
        'DocCallout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=PRIMARY
    )

    story = []

    # Title & Header
    story.append(Paragraph("Growixa: Market Pitch & GTM Playbook", title_style))
    story.append(Paragraph("A Comprehensive Guide to Positioning, Built-In Features, Competitor Comparisons, and Sales Execution", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=12))

    # Executive Summary Card
    summary_text = (
        "<b>Executive Summary:</b> Growixa is an AI-powered marketing and campaign automation platform designed for modern "
        "businesses and growth teams. It unifies high-deliverability email campaigns, intelligent audience segmentation, "
        "brand-safe AI copywriting with mandatory human approval, and multichannel automation into a fast, intuitive dashboard."
    )
    callout_data = [[Paragraph(summary_text, callout_style)]]
    callout_table = Table(callout_data, colWidths=[532])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CARD_BG),
        ('BOX', (0,0), (-1,-1), 1, SECONDARY),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 10))

    # Core Positioning Pitches
    story.append(Paragraph("1. Core Positioning & Pitch Formats", h1_style))
    story.append(Paragraph("<b>The One-Liner:</b> <i>\"Growixa is the AI growth engine that unifies high-deliverability email, smart audience segmentation, and brand-safe AI content into one intuitive dashboard.\"</i>", body_style))
    story.append(Paragraph("<b>The 30-Second Pitch:</b> Most marketing teams juggle 5 disconnected tools for CRM, AI drafting, email delivery, and analytics. Growixa replaces that fragmented stack with a unified engine: real-time segmentation, compliance-first contact management, and an AI Marketing Studio with human-in-the-loop governance so you launch campaigns 10x faster without brand risk.", body_style))

    # Built-in Product Pillars
    story.append(Paragraph("2. The 5 Built-In Feature Pillars", h1_style))

    pillars = [
        ("1. Intelligent Audience & Contact Engine", "Instant CSV bulk ingestion with automatic validation and duplicate deduplication. Dynamic real-time segmentation based on tags, user attributes, and engagement behavior. Built-in consent tracking and hard-suppression lists for GDPR/CAN-SPAM compliance."),
        ("2. AI Marketing Studio (Human-in-the-Loop)", "Context-aware AI generator for high-converting email sequences, multi-variant subject lines (curiosity, benefit, direct), and social posts. Enforces a deterministic human approval gate—AI never sends rogue emails autonomously."),
        ("3. Campaign Delivery & Scheduling Engine", "5-step streamlined campaign wizard: Recipient Selection -> AI Content -> Personalization -> Test Inbox Preview -> Scheduled/Instant Send. Dual-route sending via Postmark or Bring-Your-Own Custom SMTP for domain isolation."),
        ("4. Real-Time Delivery & Token Analytics", "Granular analytics tracking Sent, Delivered, Opens, Clicks, Bounces, and Spam Complaints. Evidence-based reporting distinguishing provider data from estimated metrics, plus real-time AI token cost metering."),
        ("5. Team Governance & Enterprise Security", "Granular Role-Based Access Control (RBAC) across 6 roles (Super Admin, Admin, Marketing Manager, Content Creator, Analyst, Viewer). Full immutable audit logging of every campaign edit, approval, and send.")
    ]

    for p_title, p_desc in pillars:
        story.append(Paragraph(f"<b>{p_title}</b>", h2_style))
        story.append(Paragraph(p_desc, body_style))

    story.append(Spacer(1, 8))

    # Competitor Comparison Table
    story.append(Paragraph("3. Competitor Comparison Battlecard", h1_style))
    table_data = [
        [
            Paragraph("<b>Capability / Dimension</b>", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
            Paragraph("<b>Growixa</b>", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
            Paragraph("<b>Brevo (Sendinblue)</b>", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
            Paragraph("<b>Mailchimp / Klaviyo</b>", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
        ],
        [
            Paragraph("<b>Native AI Marketing Studio</b>", body_style),
            Paragraph("<font color='#10B981'><b>Native & Context-Aware</b></font>", body_style),
            Paragraph("Basic Add-on", body_style),
            Paragraph("Basic Add-on", body_style),
        ],
        [
            Paragraph("<b>Human-in-the-Loop Safety</b>", body_style),
            Paragraph("<font color='#10B981'><b>Mandatory Approval Gate</b></font>", body_style),
            Paragraph("Manual copy-paste", body_style),
            Paragraph("Manual copy-paste", body_style),
        ],
        [
            Paragraph("<b>Dedicated Sending Infrastructure</b>", body_style),
            Paragraph("<font color='#10B981'><b>Postmark + Custom SMTP</b></font>", body_style),
            Paragraph("Locked to Brevo IPs", body_style),
            Paragraph("Locked to Mandrill IPs", body_style),
        ],
        [
            Paragraph("<b>Growth Roadmap</b>", body_style),
            Paragraph("<font color='#10B981'><b>Email + Social + SEO/AEO</b></font>", body_style),
            Paragraph("Email + SMS/WhatsApp", body_style),
            Paragraph("Email + Landing Pages", body_style),
        ],
        [
            Paragraph("<b>Campaign Setup Speed</b>", body_style),
            Paragraph("<font color='#10B981'><b>< 15 minutes (5-step wizard)</b></font>", body_style),
            Paragraph("30-60 min (Complex UI)", body_style),
            Paragraph("45-60 min (Bloated UI)", body_style),
        ]
    ]

    comp_table = Table(table_data, colWidths=[150, 130, 126, 126])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 10))

    # Persona Playbooks
    story.append(Paragraph("4. Persona Playbooks & Value Props", h1_style))
    story.append(Paragraph("• <b>Startup Founders & SMBs:</b> Run growth like a full marketing team—from email outreach to social—without paying agency fees or learning complex tools.", bullet_style))
    story.append(Paragraph("• <b>Growth Marketers & Demand Gen Leads:</b> Stop jumping between ChatGPT, Notion, and email senders. Draft, segment, validate, and send high-converting campaigns from a single dashboard.", bullet_style))
    story.append(Paragraph("• <b>Marketing Agencies & Freelancers:</b> Scale client campaigns with predictable deliverability, pre-built templates, and rapid AI drafting under strict brand voice controls.", bullet_style))

    # Cold Outreach Templates
    story.append(Paragraph("5. High-Converting Cold Outreach Template", h1_style))
    email_sample = (
        "<b>Subject:</b> Quick question regarding {{company_name}}'s email stack<br/><br/>"
        "Hi {{first_name}},<br/><br/>"
        "Are you currently jumping between ChatGPT for copy and your email tool to build campaigns for {{company_name}}?<br/><br/>"
        "We built Growixa to unify that entire loop:<br/>"
        "• Dynamic audience segmentation (with built-in consent & suppression)<br/>"
        "• AI Marketing Studio that drafts on-brand emails & social hooks<br/>"
        "• Human-in-the-loop approval and high-deliverability Postmark/SMTP sending<br/><br/>"
        "Teams cut campaign setup time from 3 hours to under 15 minutes while protecting domain reputation.<br/><br/>"
        "Would you be open to a 2-minute walkthrough this week?<br/><br/>"
        "Best regards,<br/>"
        "<b>[Your Name]</b> — Growixa"
    )
    email_table = Table([[Paragraph(email_sample, body_style)]], colWidths=[532])
    email_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, SECONDARY),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(email_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_path}")


def build_vc_deck_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        leftMargin=35,
        rightMargin=35,
        topMargin=45,
        bottomMargin=45
    )
    styles = getSampleStyleSheet()

    slide_title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=4
    )
    slide_subtitle_style = ParagraphStyle(
        'SlideSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceAfter=12
    )
    card_title_style = ParagraphStyle(
        'CardTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceAfter=4
    )
    card_body_style = ParagraphStyle(
        'CardBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_MAIN
    )
    body_style = ParagraphStyle(
        'SlideBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_MAIN,
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'SlideBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_MAIN,
        leftIndent=15,
        spaceAfter=4
    )

    story = []

    def make_card(title, body, width=225, height=100, border_color=SECONDARY, bg_color=CARD_BG):
        content = [
            Paragraph(f"<b>{title}</b>", card_title_style),
            Spacer(1, 3),
            Paragraph(body, card_body_style)
        ]
        t = Table([[content]], colWidths=[width])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_color),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        return t

    # ----------------------------------------------------
    # SLIDE 1: Title & Vision
    # ----------------------------------------------------
    story.append(Spacer(1, 40))
    hero_title = ParagraphStyle('HeroTitle', fontName='Helvetica-Bold', fontSize=32, leading=38, textColor=PRIMARY, alignment=1)
    hero_sub = ParagraphStyle('HeroSub', fontName='Helvetica-Bold', fontSize=15, leading=20, textColor=SECONDARY, alignment=1)
    hero_meta = ParagraphStyle('HeroMeta', fontName='Helvetica', fontSize=11, leading=16, textColor=TEXT_MUTED, alignment=1)

    story.append(Paragraph("GROWIXA", hero_title))
    story.append(Spacer(1, 10))
    story.append(Paragraph("The AI-Powered Growth & Campaign Automation Engine", hero_sub))
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="60%", thickness=2, color=SECONDARY, spaceBefore=5, spaceAfter=15))
    story.append(Paragraph("<i>Speed of AI • Precision of Human Control • Power of High Deliverability</i>", hero_meta))
    story.append(Spacer(1, 30))

    meta_table = Table([
        [
            Paragraph("<b>Target Round:</b> Seed ($750K)", card_body_style),
            Paragraph("<b>Sector:</b> B2B SaaS / MarTech / AI", card_body_style),
            Paragraph("<b>Status:</b> MVP Complete / Architecture Validated", card_body_style)
        ]
    ], colWidths=[240, 240, 240])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CARD_BG),
        ('BOX', (0,0), (-1,-1), 1, SECONDARY),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 2: The Problem
    # ----------------------------------------------------
    story.append(Paragraph("The Problem: Fragmented Tools & The AI Trust Crisis", slide_title_style))
    story.append(Paragraph("Modern growth teams are overwhelmed by disconnected software and unverified AI outputs.", slide_subtitle_style))

    c1 = make_card("1. Tool Fragmentation & Bloat", "Marketers juggle 4-6 separate tools for CRM, AI drafting, email sending, and analytics—wasting time and paying $500+/mo in subscription fees.", 228)
    c2 = make_card("2. The 'Copy-Paste' AI Gap", "80% of marketers draft in ChatGPT in silos, losing context, contact variables, and audience segmentation when moving to email tools.", 228)
    c3 = make_card("3. Unsupervised AI Risk", "Autonomous AI tools risk sending hallucinations and spam, burning sender reputation and violating strict privacy regulations (GDPR/CAN-SPAM).", 228)

    row1 = Table([[c1, c2, c3]], colWidths=[240, 240, 240])
    row1.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(row1)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>The Core Result:</b> Marketers waste 3+ hours per campaign, suffer poor deliverability, and live in constant fear of AI errors reaching real inboxes.", body_style))
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 3: The Market Opportunity
    # ----------------------------------------------------
    story.append(Paragraph("Market Opportunity: $65B Global MarTech Transformation", slide_title_style))
    story.append(Paragraph("A massive shift from legacy point solutions to integrated, AI-native growth platforms.", slide_subtitle_style))

    m1 = make_card("TAM: $65B", "Total Global Marketing Automation, CRM & Email Software Market.", 228, bg_color=BG_LIGHT, border_color=PRIMARY)
    m2 = make_card("SAM: $18B", "SMB & Mid-Market Cloud Marketing Software in North America, Europe, and Asia-Pacific.", 228, bg_color=BG_LIGHT, border_color=SECONDARY)
    m3 = make_card("SOM: $1.2B", "Fast-growing digital agencies, startups, creators, and high-velocity B2B SaaS teams.", 228, bg_color=BG_LIGHT, border_color=SUCCESS)

    row_m = Table([[m1, m2, m3]], colWidths=[240, 240, 240])
    story.append(row_m)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Tailwinds Driving Growixa:</b>", card_title_style))
    story.append(Paragraph("• <b>Rise of Generative AI:</b> Teams demand native AI generation directly inside campaign delivery tools.", bullet_style))
    story.append(Paragraph("• <b>Deliverability Crackdowns:</b> Google and Yahoo's stricter authentication rules require pristine sender isolation.", bullet_style))
    story.append(Paragraph("• <b>SaaS Consolidation:</b> Businesses are actively replacing fragmented 5-tool stacks with all-in-one platforms.", bullet_style))
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 4: The Solution (Growixa)
    # ----------------------------------------------------
    story.append(Paragraph("The Solution: Growixa Unifies the Entire Growth Stack", slide_title_style))
    story.append(Paragraph("Combining the speed of generative AI with mandatory human control and enterprise deliverability.", slide_subtitle_style))

    s1 = make_card("Audience & Contact Engine", "Clean CSV imports, dynamic real-time segmentation, custom attributes, and automated GDPR/CCPA suppression.", 228)
    s2 = make_card("AI Marketing Studio", "High-converting email sequences, multi-variant subject lines, brand voice enforcement, and mandatory human review.", 228)
    s3 = make_card("High-Deliverability Engine", "5-step wizard, test preview sends, Postmark delivery + Custom SMTP routing, and live engagement metrics.", 228)

    row_s = Table([[s1, s2, s3]], colWidths=[240, 240, 240])
    story.append(row_s)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>The Growixa Workflow:</b> <i>Audience Segments -> AI Drafts Campaign -> Manager Reviews & Approves -> High-Deliverability Dispatch -> Live Analytics</i>", ParagraphStyle('Flow', fontName='Helvetica-Bold', fontSize=10, textColor=SECONDARY)))
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 5: Built-In Product Capabilities
    # ----------------------------------------------------
    story.append(Paragraph("Built-In Product Architecture & Enterprise Capabilities", slide_title_style))
    story.append(Paragraph("Production-ready foundation engineered for scale, reliability, and security.", slide_subtitle_style))

    p1 = make_card("Frictionless 5-Step Wizard", "Audience Selection -> AI Content -> Personalization Tags -> Test Inbox -> Schedule/Deliver.", 228)
    p2 = make_card("Dual-Route Sending", "Postmark API + Custom SMTP support for complete sender reputation and IP isolation.", 228)
    p3 = make_card("Granular Team RBAC", "6 distinct user roles (Super Admin to Viewer) with server-side permission enforcement.", 228)

    p4 = make_card("Immutable Audit Trails", "Every draft edit, AI prompt, approval, and send is logged with exact timestamps and actor IDs.", 228)
    p5 = make_card("AI Token Cost Metering", "Real-time AI compute tracking with strict budget guardrails to protect customer margins.", 228)
    p6 = make_card("Complete Data Isolation", "Tenant data is strictly partitioned by account_id, ensuring zero cross-customer data leakage.", 228)

    grid = Table([[p1, p2, p3], [p4, p5, p6]], colWidths=[240, 240, 240])
    grid.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(grid)
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 6: Competitive Moat & Battlecard
    # ----------------------------------------------------
    story.append(Paragraph("Competitive Landscape: Why Growixa Wins", slide_title_style))
    story.append(Paragraph("Growixa is positioned uniquely at the intersection of AI Copilots and Delivery Infrastructure.", slide_subtitle_style))

    comp_deck_data = [
        [
            Paragraph("<b>Dimension</b>", ParagraphStyle('THD', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
            Paragraph("<b>Growixa</b>", ParagraphStyle('THD', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
            Paragraph("<b>Brevo / Mailchimp</b>", ParagraphStyle('THD', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
            Paragraph("<b>Jasper / Copy.ai</b>", ParagraphStyle('THD', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white))
        ],
        [
            Paragraph("<b>Core Focus</b>", card_body_style),
            Paragraph("<b>AI Growth & Delivery Engine</b>", card_body_style),
            Paragraph("Legacy Email/CRM", card_body_style),
            Paragraph("Isolated AI Copywriting", card_body_style)
        ],
        [
            Paragraph("<b>AI Integration</b>", card_body_style),
            Paragraph("<font color='#10B981'><b>Native AI Studio in Send Flow</b></font>", card_body_style),
            Paragraph("Basic add-on / prompt box", card_body_style),
            Paragraph("Text editor only (No sending)", card_body_style)
        ],
        [
            Paragraph("<b>Content Governance</b>", card_body_style),
            Paragraph("<font color='#10B981'><b>Mandatory Human Approval Gate</b></font>", card_body_style),
            Paragraph("Manual copy-paste", card_body_style),
            Paragraph("None (External tool)", card_body_style)
        ],
        [
            Paragraph("<b>Infrastructure</b>", card_body_style),
            Paragraph("<font color='#10B981'><b>Postmark + Custom SMTP</b></font>", card_body_style),
            Paragraph("Shared IP network", card_body_style),
            Paragraph("N/A", card_body_style)
        ],
        [
            Paragraph("<b>Future Trajectory</b>", card_body_style),
            Paragraph("<font color='#10B981'><b>Email -> Social -> SEO/AEO</b></font>", card_body_style),
            Paragraph("Email & WhatsApp only", card_body_style),
            Paragraph("Text & Image Generation", card_body_style)
        ]
    ]

    deck_table = Table(comp_deck_data, colWidths=[130, 200, 195, 195])
    deck_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('PADDING', (0,0), (-1,-1), 4.5),
    ]))
    story.append(deck_table)
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 7: Business Model & Unit Economics
    # ----------------------------------------------------
    story.append(Paragraph("Business Model & Unit Economics", slide_title_style))
    story.append(Paragraph("Scalable SaaS Subscription + Usage-Based AI Expansion Revenue", slide_subtitle_style))

    b1 = make_card("Starter Plan ($29/mo)", "• Up to 5,000 Contacts<br/>• 50,000 Emails / Month<br/>• AI Copywriting Studio<br/>• 2 Team Seats", 228)
    b2 = make_card("Growth Plan ($79/mo)", "• Up to 25,000 Contacts<br/>• 250,000 Emails / Month<br/>• Multi-Variant AI Engine<br/>• Custom SMTP + 5 Seats", 228, bg_color=CARD_BG, border_color=SECONDARY)
    b3 = make_card("Scale / Enterprise ($199+/mo)", "• Unlimited Contacts<br/>• Dedicated IP Sending<br/>• Advanced RBAC & Audit<br/>• Custom AI Fine-Tuning", 228)

    row_b = Table([[b1, b2, b3]], colWidths=[240, 240, 240])
    story.append(row_b)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Key Financial Drivers:</b>", card_title_style))
    story.append(Paragraph("• <b>High Gross Margins:</b> Projected 80%+ gross margin on software subscriptions.", bullet_style))
    story.append(Paragraph("• <b>Expansion Revenue:</b> Consumption-based AI token packs and high-volume email add-ons.", bullet_style))
    story.append(Paragraph("• <b>Low Churn Dynamics:</b> Embedded contact data and campaign history create high platform stickiness.", bullet_style))
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 8: Go-To-Market Strategy
    # ----------------------------------------------------
    story.append(Paragraph("Go-To-Market Strategy (GTM)", slide_title_style))
    story.append(Paragraph("Multi-pronged growth engine combining PLG, outbound sales, and ecosystem partnerships.", slide_subtitle_style))

    g1 = make_card("1. Product-Led Growth (PLG)", "Frictionless self-service signup with a generous free trial. Users launch their first AI campaign in under 5 minutes.", 228)
    g2 = make_card("2. Agency Partner Channel", "Equip digital marketing agencies with multi-account tools to manage client campaigns at scale.", 228)
    g3 = make_card("3. Targeted B2B Outbound", "Direct outreach to fast-growing startups and growth leads suffering from Mailchimp/Brevo bloat.", 228)

    row_g = Table([[g1, g2, g3]], colWidths=[240, 240, 240])
    story.append(row_g)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Content & Community Flywheel:</b> Publishing proprietary benchmarks on AI email deliverability, high-converting templates, and growth case studies to drive organic inbound.", body_style))
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 9: Technology & Milestones Achieved
    # ----------------------------------------------------
    story.append(Paragraph("Technology & Milestones Achieved", slide_title_style))
    story.append(Paragraph("Robust, enterprise-grade architecture already built, tested, and validated.", slide_subtitle_style))

    story.append(Paragraph("• <b>Production-Grade Web Application:</b> Full Next.js frontend with modern Tailwind/design system.", bullet_style))
    story.append(Paragraph("• <b>Scalable Microservice Backend:</b> FastAPI Python backend with PostgreSQL and Redis task workers.", bullet_style))
    story.append(Paragraph("• <b>Dual Email Delivery Infrastructure:</b> Fully integrated Postmark adapter + Custom SMTP provider engine.", bullet_style))
    story.append(Paragraph("• <b>AI Studio & Human Governance:</b> Working AI generation pipelines with mandatory approval gates.", bullet_style))
    story.append(Paragraph("• <b>Automated CI/CD & Deployments:</b> Multi-environment VPS setup with Caddy auto-SSL and Docker Compose.", bullet_style))
    story.append(Paragraph("• <b>Enterprise Security Baseline:</b> RBAC, encrypted credentials, CSRF/XSS protection, and comprehensive audit trails.", bullet_style))
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 10: Product Roadmap
    # ----------------------------------------------------
    story.append(Paragraph("Long-Term Product Roadmap", slide_title_style))
    story.append(Paragraph("Expanding from Email Marketing into an Autonomous Cross-Channel Growth System.", slide_subtitle_style))

    r1 = make_card("Phase 1: Foundation (Current)", "• AI Email Marketing & Studio<br/>• Audience Segmentation & Consent<br/>• Postmark & Custom SMTP Routing<br/>• Team Roles & Audit Governance", 228, bg_color=CARD_BG, border_color=SECONDARY)
    r2 = make_card("Phase 2: Multichannel & SEO", "• Social Media Auto-Publishing<br/>• Website Intelligence & SEO Auditing<br/>• AEO (Answer Engine Optimization)<br/>• GEO (Generative Engine Optimization)", 228)
    r3 = make_card("Phase 3: Autonomous Growth", "• Multi-Agent Growth Workflows<br/>• CMS Integration (WP / GitHub)<br/>• Predictive Audience Churn Alerts<br/>• Autonomous Campaign Tuning", 228)

    row_r = Table([[r1, r2, r3]], colWidths=[240, 240, 240])
    story.append(row_r)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Strategic Vision:</b> Growixa will become the central operating system where a company manages its entire digital growth lifecycle without stitching tools together.", body_style))
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 11: Team & Execution DNA
    # ----------------------------------------------------
    story.append(Paragraph("Team & Execution Velocity", slide_title_style))
    story.append(Paragraph("Engineered for rapid iteration, strict code quality, and security excellence.", slide_subtitle_style))

    t1 = make_card("Full-Stack & Cloud Architecture", "Deep background in designing highly available distributed backends, microservices, and modern web apps.", 228)
    t2 = make_card("AI & Growth Engineering", "Specialized expertise in LLM agent orchestration, prompt safety guardrails, and conversion copywriting.", 228)
    t3 = make_card("Enterprise Deliverability", "Proven experience in SMTP protocols, IP reputation warming, DNS authentication (SPF, DKIM, DMARC), and compliance.", 228)

    row_t = Table([[t1, t2, t3]], colWidths=[240, 240, 240])
    story.append(row_t)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Execution Principles:</b> Fast delivery cycles, zero-compromise security, human-in-the-loop AI safety, and customer-first engineering.", body_style))
    story.append(PageBreak())

    # ----------------------------------------------------
    # SLIDE 12: The Ask & Use of Funds
    # ----------------------------------------------------
    story.append(Paragraph("The Ask: $750,000 Seed Round", slide_title_style))
    story.append(Paragraph("Accelerating Product Expansion and Customer Acquisition", slide_subtitle_style))

    u1 = make_card("45% Product & Engineering", "• Expand SEO/AEO/GEO engine<br/>• Multichannel social connectors<br/>• Advanced predictive segmentation", 228, bg_color=CARD_BG, border_color=PRIMARY)
    u2 = make_card("35% GTM & Acquisition", "• PLG onboarding optimization<br/>• Targeted B2B outbound engine<br/>• Agency partner channel program", 228, bg_color=CARD_BG, border_color=SECONDARY)
    u3 = make_card("20% Infrastructure & Ops", "• Dedicated sending IP infrastructure<br/>• Security audits & SOC 2 compliance<br/>• High-availability operations", 228, bg_color=CARD_BG, border_color=SUCCESS)

    row_u = Table([[u1, u2, u3]], colWidths=[240, 240, 240])
    story.append(row_u)
    story.append(Spacer(1, 25))

    contact_table = Table([
        [
            Paragraph("<b>Join us in building the future of AI-powered growth.</b><br/>Contact: <b>founders@growixa.com</b> | Website: <b>https://growixa.com</b>", ParagraphStyle('Contact', fontName='Helvetica-Bold', fontSize=10, textColor=PRIMARY, alignment=1))
        ]
    ], colWidths=[720])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, SECONDARY),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(contact_table)

    doc.build(story, canvasmaker=SlideCanvas)
    print(f"Successfully generated: {output_path}")


if __name__ == "__main__":
    out_dir = "/Users/ravi/Projects/growixa/docs/13-marketing"
    os.makedirs(out_dir, exist_ok=True)

    playbook_pdf = os.path.join(out_dir, "Growixa_Product_Pitch_and_GTM_Playbook.pdf")
    vc_deck_pdf = os.path.join(out_dir, "Growixa_Investor_VC_Pitch_Deck.pdf")

    build_playbook_pdf(playbook_pdf)
    build_vc_deck_pdf(vc_deck_pdf)
