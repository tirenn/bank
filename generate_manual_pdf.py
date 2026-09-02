import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.HexColor('#64748B'))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, 'NOVA DIGITAL BANK  |  SYSTEM MANUAL & OPERATIONAL POLICY GUIDE')
            self.setStrokeColor(colors.HexColor('#CBD5E1'))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
        
        # Footer
        page_str = f'Page {self._pageNumber} of {page_count}'
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, 'CONFIDENTIAL & PROPRIETARY  —  NOVA BANKING CORP.')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()

def create_manual(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=64,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor('#0F172A')
    brand_blue = colors.HexColor('#0284C7')
    text_dark = colors.HexColor('#1E293B')
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=brand_blue,
        spaceAfter=8
    )
    
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=brand_blue,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_dark,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_dark,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=text_dark
    )

    story = []

    # COVER / HEADER
    story.append(Paragraph('NOVA DIGITAL BANK', subtitle_style))
    story.append(Paragraph('Comprehensive System Manual & Banking Policy Guide', title_style))
    story.append(Paragraph('<b>Version:</b> 4.2.0-PROD &nbsp;|&nbsp; <b>Classification:</b> Official Operations Manual & Customer Guide &nbsp;|&nbsp; <b>Effective Date:</b> 2026-2027', body_style))
    story.append(HRFlowable(width='100%', thickness=1.5, color=brand_blue, spaceBefore=4, spaceAfter=8))

    abstract_html = '<b>Executive Summary:</b> This document establishes the authoritative operational guidelines, fee structures, compliance requirements, transactional limits, security controls, and end-user system navigation procedures for Nova Digital Bank. It serves as both the canonical reference for customer accounts and the knowledge base for Nova\'s AI Banking Assistant.'
    callout_data = [[Paragraph(abstract_html, callout_style)]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F9FF')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#BAE6FD')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 6))

    # SECTION 1: ACCOUNT ARCHITECTURE
    story.append(Paragraph('1. Customer Account Architecture & Account Types', h1_style))
    story.append(Paragraph('Nova Bank provides three primary tiers of digital retail and commercial accounts. Every account is provisioned with an international IBAN, routing transit number, and cryptographic ledger tracking.', body_style))
    
    acc_table_data = [
        [Paragraph('Account Tier', table_header_style), Paragraph('Target Customer', table_header_style), Paragraph('Minimum Deposit', table_header_style), Paragraph('Monthly Maintenance', table_header_style), Paragraph('Standard APY', table_header_style)],
        [Paragraph('<b>Standard Checking</b>', table_cell_style), Paragraph('Everyday transactions, salary deposits', table_cell_style), Paragraph('.00', table_cell_style), Paragraph('.00 (Free)', table_cell_style), Paragraph('0.10%', table_cell_style)],
        [Paragraph('<b>High-Yield Savings</b>', table_cell_style), Paragraph('Wealth accumulation, emergency fund', table_cell_style), Paragraph('.00', table_cell_style), Paragraph('.00 (Free)', table_cell_style), Paragraph('4.75% Compounded Daily', table_cell_style)],
        [Paragraph('<b>Premium Wealth Tier</b>', table_cell_style), Paragraph('High net-worth & multi-currency holders', table_cell_style), Paragraph(',000.00', table_cell_style), Paragraph('.00 (Waived at +)', table_cell_style), Paragraph('5.20% APY + VIP Perks', table_cell_style)]
    ]
    t1 = Table(acc_table_data, colWidths=[100, 130, 80, 100, 94])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 6))

    # SECTION 2: FEE SCHEDULE & LIMITS
    story.append(Paragraph('2. Complete Fee Schedule & Transaction Limits', h1_style))
    story.append(Paragraph('All fees are evaluated and settled automatically in real time according to the following schedule:', body_style))

    fee_table_data = [
        [Paragraph('Operation / Service', table_header_style), Paragraph('Standard Tier Fee', table_header_style), Paragraph('Processing Window', table_header_style), Paragraph('Daily Limit (Per User)', table_header_style)],
        [Paragraph('Internal Account Transfer (P2P)', table_cell_style), Paragraph('.00 (Always Free)', table_cell_style), Paragraph('Instant (Sub-second)', table_cell_style), Paragraph(',000.00 / day', table_cell_style)],
        [Paragraph('Domestic ACH Wire Transfer', table_cell_style), Paragraph('.00 standard / .00 express', table_cell_style), Paragraph('ACH: 1-2 days / Same-day', table_cell_style), Paragraph(',000.00 / day', table_cell_style)],
        [Paragraph('International SWIFT Outbound', table_cell_style), Paragraph('.00 flat + 0.3% FX spread', table_cell_style), Paragraph('1 to 3 Business Days', table_cell_style), Paragraph(',000.00 / day', table_cell_style)],
        [Paragraph('ATM Cash Withdrawal (In-Network)', table_cell_style), Paragraph('.00 (All 55k+ Allpoint ATMs)', table_cell_style), Paragraph('Instant Cash Dispense', table_cell_style), Paragraph(',500.00 / day', table_cell_style)],
        [Paragraph('Overdraft Cushion Protection', table_cell_style), Paragraph('.00 up to -.00 cushion', table_cell_style), Paragraph('Immediate Auto-coverage', table_cell_style), Paragraph('Max -.00 balance', table_cell_style)]
    ]
    t2 = Table(fee_table_data, colWidths=[140, 130, 114, 120])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 6))

    # SECTION 3: SECURITY & FRAUD PROTECTION
    story.append(Paragraph('3. Security Architecture, Cards & Account Freezing', h1_style))
    story.append(Paragraph('<b>Card Management & Virtual Number Generation:</b>', h2_style))
    story.append(Paragraph('• <b>Instant Virtual Cards:</b> Users may generate up to 5 disposable virtual cards per calendar month directly from the Cards dashboard. Virtual cards support custom single-transaction and monthly caps for secure e-commerce.', bullet_style))
    story.append(Paragraph('• <b>Physical Debit Cards:</b> Shipped via tracked courier within 3-5 business days upon account creation. Supports contactless NFC and EMV chip PIN.', bullet_style))
    story.append(Paragraph('• <b>Emergency Account & Card Freeze:</b> If a card is lost or unauthenticated charges occur, users or support personnel can issue an instant freeze command. A frozen card immediately rejects all authorizations while allowing inbound deposits.', bullet_style))
    story.append(Paragraph('• <b>FDIC Insurance & Cryptographic Encryption:</b> Deposits are insured up to ,000 per depositor. Data at rest is encrypted with AES-256-GCM; communications enforce TLS 1.3.', bullet_style))
    story.append(Spacer(1, 6))

    # SECTION 4: WEALTH, FOREX & LOANS
    story.append(Paragraph('4. Wealth, Multi-Currency Forex & Lending Formulas', h1_style))
    story.append(Paragraph('<b>Multi-Currency Engine:</b> Nova supports real-time multi-currency wallets in USD, EUR, GBP, JPY, CAD, AUD, CHF, and SGD. Interbank mid-market exchange rates are streamed with a 0.3% fixed spread.', body_style))
    story.append(Paragraph('<b>Personal Loan & Mortgage Underwriting Rules:</b>', h2_style))
    story.append(Paragraph('• <b>Borrowing Amounts:</b> Unsecured personal loans range from ,000 to ,000 with repayment tenors of 12, 24, 36, 48, or 60 months.', bullet_style))
    story.append(Paragraph('• <b>Interest Rate Range:</b> Annual Percentage Rate (APR) begins at 6.49% for prime tier credit scores (740+) and caps at 18.99% for standard credit scores.', bullet_style))
    story.append(Paragraph('• <b>Monthly Installment Formula:</b> Monthly payment <i>M</i> is calculated via standard amortization:', bullet_style))
    story.append(Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;<b>M = P * [r(1 + r)^n] / [(1 + r)^n - 1]</b> (where <i>P</i> = Principal, <i>r</i> = Monthly Interest Rate, <i>n</i> = Number of Payments)', callout_style))
    story.append(Spacer(1, 6))

    # SECTION 5: HOW TO USE THIS SYSTEM (STEP-BY-STEP)
    story.append(Paragraph('5. User Operating Guide — How to Use This System', h1_style))
    story.append(Paragraph('This step-by-step operating guide details how customers and administrators navigate the Nova Banking Web Platform and interact with the AI Assistant:', body_style))

    story.append(Paragraph('Step 1: Logging In & Authentication', h2_style))
    story.append(Paragraph('1. Open the Nova Banking Portal in your web browser (default URL: <code>http://localhost:5173</code>).', bullet_style))
    story.append(Paragraph('2. Enter your registered email (e.g. <code>john.doe@bank.com</code>) and secure password (e.g. <code>password123</code>).', bullet_style))
    story.append(Paragraph('3. If Multi-Factor Authentication (MFA) is enabled, enter the 6-digit TOTP code sent to your authenticator app.', bullet_style))

    story.append(Paragraph('Step 2: Managing Accounts & Reviewing Balances', h2_style))
    story.append(Paragraph('1. Upon authentication, you will be directed to the <b>Dashboard Overview</b>, displaying your active accounts, primary checking balance, high-yield savings, and recent activity.', bullet_style))
    story.append(Paragraph('2. To open an additional account (e.g. High-Yield Savings or Euro Wallet), click <b>\'Open New Account\'</b> in the top-right header, select the currency and account type, and confirm.', bullet_style))

    story.append(Paragraph('Step 3: Sending Transfers & Managing Payees', h2_style))
    story.append(Paragraph('1. Click <b>\'Transfers\'</b> on the sidebar navigation.', bullet_style))
    story.append(Paragraph('2. Select the <b>Source Account</b> from which funds will be deducted.', bullet_style))
    story.append(Paragraph('3. Enter the <b>Destination Account Number</b> or pick from your <b>Saved Payees</b> list.', bullet_style))
    story.append(Paragraph('4. Input the transfer amount and optional description, then click <b>\'Review & Execute Transfer\'</b>.', bullet_style))

    story.append(Paragraph('Step 4: Interacting with Nova\'s AI Banking Assistant', h2_style))
    story.append(Paragraph('Nova integrates a fully conversational, tool-calling AI assistant powered by autonomous SubAgents and ChromaDB RAG. You can interact with the assistant via the floating chat widget on any screen:', body_style))
    story.append(Paragraph('• <b>Account Operations:</b> Type <i>\'What is my current balance?\'</i> or <i>\'Show my last 5 transactions\'</i>. The AI will autonomously call backend banking tools to fetch your real-time balances.', bullet_style))
    story.append(Paragraph('• <b>Transferring Money:</b> Type <i>\'Transfer  to account 100002 for dinner\'</i>. The AI will inspect parameters, initiate the transfer, and provide an interactive confirmation receipt.', bullet_style))
    story.append(Paragraph('• <b>Security Controls:</b> Type <i>\'Freeze my debit card immediately\'</i> or <i>\'Set my daily spending limit to \'</i>.', bullet_style))
    story.append(Paragraph('• <b>Currency Conversion & Loan Calculations:</b> Type <i>\'Convert 500 USD to EUR\'</i> or <i>\'Calculate monthly payment for a ,000 loan at 7.5% for 36 months\'</i>.', bullet_style))
    story.append(Paragraph('• <b>Policy & Fee Inquiries:</b> Type <i>\'What are the wire transfer fees?\'</i> or <i>\'How does high-yield savings APY work?\'</i>. The AI will query the ChromaDB Vector Store and answer with citation accuracy.', bullet_style))

    story.append(Paragraph('Step 5: Uploading & Ingesting Documents into RAG Knowledge Base', h2_style))
    story.append(Paragraph('1. Navigate to the <b>Knowledge Base / RAG Admin</b> view in the platform.', bullet_style))
    story.append(Paragraph('2. Click <b>\'Upload Document\'</b> and select a policy document or PDF (such as this manual).', bullet_style))
    story.append(Paragraph('3. Select your preferred chunking strategy: <b>Dynamic LLM Semantic Chunking</b> (recommended for complex multi-topic docs) or <b>Fixed-Window Chunking</b>.', bullet_style))
    story.append(Paragraph('4. Click <b>\'Ingest into ChromaDB\'</b>. The system will atomically chunk, embed, and index the document. Once completed, the AI assistant will immediately answer customer queries using the new knowledge.', bullet_style))

    story.append(Paragraph('Step 6: Security Best Practices & Support Escalation', h2_style))
    story.append(Paragraph('• Never share your banking password, PIN, or MFA tokens with anyone.', bullet_style))
    story.append(Paragraph('• If you detect unauthorized access, immediately freeze your accounts via the AI chat or settings menu.', bullet_style))
    story.append(Paragraph('• For human support escalation, contact Nova Support 24/7 at <code>support@novabank.com</code> or <code>1-800-555-NOVA</code>.', bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f'Successfully generated manual at: {output_path}')

if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'nova_bank_system_manual.pdf'
    create_manual(output)
