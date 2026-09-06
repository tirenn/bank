import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page count
    along with running header and footer on every page.
    """
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
        self.setFont('Helvetica-Bold', 7.5)
        self.setFillColor(colors.HexColor('#0F172A'))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 752, 'TIRENN CORE BANKING & AI COPILOT')
            self.setFont('Helvetica', 7.5)
            self.setFillColor(colors.HexColor('#64748B'))
            self.drawRightString(558, 752, 'PANDUAN OPERASIONAL RESMI, FITUR AI & FAQ')
            self.setStrokeColor(colors.HexColor('#0D9488'))
            self.setLineWidth(1)
            self.line(54, 745, 558, 745)

        # Running Footer (all pages)
        self.setFont('Helvetica', 7.5)
        self.setFillColor(colors.HexColor('#64748B'))
        self.drawString(54, 34, 'TIRENN CORE BANKING CORP. | CONFIDENTIAL & KNOWLEDGE BASE REFERENCE')
        page_str = f'Halaman {self._pageNumber} dari {page_count}'
        self.drawRightString(558, 34, page_str)
        self.setStrokeColor(colors.HexColor('#E2E8F0'))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)

        self.restoreState()


def create_manual(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=56
    )

    styles = getSampleStyleSheet()

    # Brand Colors
    c_navy = colors.HexColor('#0F172A')
    c_teal = colors.HexColor('#0D9488')
    c_emerald = colors.HexColor('#059669')
    c_blue = colors.HexColor('#0284C7')
    c_purple = colors.HexColor('#7C3AED')
    c_dark = colors.HexColor('#1E293B')
    c_gray = colors.HexColor('#64748B')
    c_bg_light = colors.HexColor('#F8FAFC')
    c_border = colors.HexColor('#CBD5E1')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_navy,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_teal,
        spaceAfter=6
    )

    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14.5,
        textColor=c_navy,
        spaceBefore=11,
        spaceAfter=4.5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12.5,
        textColor=c_teal,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=c_dark,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=c_dark,
        leftIndent=14,
        firstLineIndent=-9,
        spaceAfter=2.5
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10.5,
        textColor=c_navy
    )

    ai_prompt_style = ParagraphStyle(
        'AiPrompt',
        parent=styles['Normal'],
        fontName='Helvetica-BoldOblique',
        fontSize=7.5,
        leading=10.5,
        textColor=c_blue,
        leftIndent=12,
        spaceAfter=2.5
    )

    faq_q_style = ParagraphStyle(
        'FaqQuestion',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=c_navy,
        spaceBefore=5.5,
        spaceAfter=2,
        keepWithNext=True
    )

    faq_a_style = ParagraphStyle(
        'FaqAnswer',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=c_dark,
        leftIndent=10,
        spaceAfter=4.5
    )

    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.white
    )

    tc_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9.5,
        textColor=c_dark
    )

    story = []

    # =========================================================================
    # COVER & HEADER BLOCK
    # =========================================================================
    story.append(Paragraph('TIRENN CORE BANKING & AI FINANCIAL INTELLIGENCE', subtitle_style))
    story.append(Paragraph('Panduan Lengkap Pengguna, Eksplorasi Fitur Chat AI & FAQ Sistem', title_style))
    story.append(Paragraph(
        '<b>Versi Sistem:</b> 2.6.0-PROD &nbsp;|&nbsp; '
        '<b>Klasifikasi:</b> Manual Nasabah, Panduan Fitur Copilot & Repositori RAG &nbsp;|&nbsp; '
        '<b>Masa Berlaku:</b> 2026 - 2027', body_style
    ))
    story.append(HRFlowable(width='100%', thickness=2, color=c_teal, spaceBefore=4, spaceAfter=8))

    summary_box = (
        '<b>Ringkasan Panduan:</b> Dokumen ini menyajikan panduan operasional komprehensif Tirenn Core Banking '
        'sekaligus menjadi basis data semantik resmi (RAG Vector Knowledge Base) bagi asisten otonom <b>Tirenn Copilot</b>. '
        'Dokumen ini mencakup: arsitektur multi-rekening nasabah, suku bunga dan jadwal biaya, panduan langkah-demi-langkah '
        'pengoperasian web, <b>eksplorasi mendalam seluruh fitur yang dapat diakses via Chat AI beserta instruksi penggunaannya</b>, '
        'serta direktori lengkap 21+ Tanya Jawab (FAQ) resmi perbankan digital.'
    )
    callout_data = [[Paragraph(summary_box, callout_style)]]
    t_callout = Table(callout_data, colWidths=[504])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FDFA')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#99F6E4')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_callout)
    story.append(Spacer(1, 8))

    # =========================================================================
    # BAB 1: ARSITEKTUR AKUN & INFORMASI PRODUK
    # =========================================================================
    story.append(Paragraph('1. Struktur Akun Nasabah, Suku Bunga & Biaya Layanan', h1_style))
    story.append(Paragraph(
        'Tirenn Core Banking menyediakan ekosistem rekening multi-tingkat berbasis buku besar terdistribusi dengan '
        'jaminan integritas transaksi ACID. Setiap rekening dilengkapi nomor unik 10 digit, kode bank clearing, serta '
        'enkripsi saldo berbasis data warehouse.', body_style
    ))

    acc_data = [
        [Paragraph('Tipe Rekening', th_style), Paragraph('Fungsi Utama', th_style), Paragraph('Setoran Awal Min.', th_style), Paragraph('Biaya Admin Bulanan', th_style), Paragraph('Suku Bunga (APY)', th_style)],
        [Paragraph('<b>Standard Checking</b>', tc_style), Paragraph('Operasional harian, belanja kartu debit, transfer rutin', tc_style), Paragraph('$10.00', tc_style), Paragraph('$0.00 (Gratis Selamanya)', tc_style), Paragraph('0.25% p.a.', tc_style)],
        [Paragraph('<b>High-Yield Savings</b>', tc_style), Paragraph('Akumulasi tabungan masa depan, dana darurat liquid', tc_style), Paragraph('$25.00', tc_style), Paragraph('$0.00 (Bebas Biaya)', tc_style), Paragraph('4.25% APY (Bunga Harian)', tc_style)],
        [Paragraph('<b>Certificate of Deposit (6 Bln)</b>', tc_style), Paragraph('Simpanan berjangka tetap tenor 6 bulan', tc_style), Paragraph('$500.00', tc_style), Paragraph('$0.00', tc_style), Paragraph('4.75% Fixed APR', tc_style)],
        [Paragraph('<b>Certificate of Deposit (12 Bln)</b>', tc_style), Paragraph('Simpanan berjangka tetap tenor 12 bulan', tc_style), Paragraph('$1,000.00', tc_style), Paragraph('$0.00', tc_style), Paragraph('5.10% Fixed APR', tc_style)],
    ]
    t_acc = Table(acc_data, colWidths=[110, 150, 75, 90, 79])
    t_acc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_acc)
    story.append(Spacer(1, 6))

    story.append(Paragraph('Biaya Transaksi & Batas Limit Harian (Transaction Limits):', h2_style))
    fee_data = [
        [Paragraph('Jenis Transaksi', th_style), Paragraph('Biaya Administrasi', th_style), Paragraph('Waktu Pemrosesan', th_style), Paragraph('Limit Transaksi Harian', th_style)],
        [Paragraph('Transfer Internal P2P (Sesama Tirenn)', tc_style), Paragraph('<b>$0.00 (Gratis)</b>', tc_style), Paragraph('Real-time (Sub-detik)', tc_style), Paragraph('$50,000.00 / hari', tc_style)],
        [Paragraph('Transfer Domestik Antar Bank (ACH/Clearing)', tc_style), Paragraph('Standard: $0.00 / Express: $5.00', tc_style), Paragraph('1-2 Hari Kerja / Hari yang Sama', tc_style), Paragraph('$25,000.00 / hari', tc_style)],
        [Paragraph('Transfer Internasional (SWIFT Outbound)', tc_style), Paragraph('$15.00 flat + 0.5% FX Spread', tc_style), Paragraph('1-3 Hari Kerja', tc_style), Paragraph('$10,000.00 / hari', tc_style)],
        [Paragraph('Penarikan Tunai ATM (Jaringan Allpoint/Mitra)', tc_style), Paragraph('$0.00 (Gratis di seluruh jaringan mitra)', tc_style), Paragraph('Instan di Mesin ATM', tc_style), Paragraph('$2,500.00 / hari', tc_style)],
        [Paragraph('Penerbitan Kartu Debit Fisik & Virtual', tc_style), Paragraph('$0.00 kartu pertama & virtual gratis', tc_style), Paragraph('Virtual: Instan / Fisik: 3 hari', tc_style), Paragraph('Sesuai limit saldo akun', tc_style)],
    ]
    t_fee = Table(fee_data, colWidths=[140, 120, 120, 124])
    t_fee.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_fee)
    story.append(Spacer(1, 8))

    # =========================================================================
    # BAB 2: CARA MENGGUNAKAN SISTEM BANK (STEP-BY-STEP USER GUIDE)
    # =========================================================================
    story.append(Paragraph('2. Panduan Lengkap Penggunaan Sistem Web Bank untuk Nasabah', h1_style))
    story.append(Paragraph(
        'Bagian ini memandu Anda dalam mengoperasikan portal perbankan Tirenn melalui peramban (browser) web:', body_style
    ))

    # Panduan 1: Registrasi & Login
    story.append(Paragraph('Langkah 1: Registrasi Akun Baru & Otentikasi Masuk (Login)', h2_style))
    story.append(Paragraph('• <b>Pendaftaran Mandiri:</b> Buka portal perbankan di browser Anda. Klik tombol <i>\'Create Account\'</i> pada modal otentikasi. Masukkan Nama Lengkap sesuai KTP/Paspor, Alamat Email valid, Nomor Telepon, dan Kata Sandi yang aman.', bullet_style))
    story.append(Paragraph('• <b>Standar Keamanan Sandi:</b> Kata sandi wajib terdiri dari minimal 8 karakter dengan kombinasi huruf besar, huruf kecil, angka, dan karakter spesial untuk menjaga keamanan brankas digital Anda.', bullet_style))
    story.append(Paragraph('• <b>Akun Uji Coba Demo:</b> Untuk tujuan evaluasi, sistem menyediakan akun siap pakai: Nasabah <code>john.doe@bank.com</code> (Password: <code>password123</code>) atau Administrator <code>admin@bank.com</code> (Password: <code>password123</code>).', bullet_style))

    # Panduan 2: Navigasi Dashboard
    story.append(Paragraph('Langkah 2: Menjelajahi Dashboard & Memantau Portofolio', h2_style))
    story.append(Paragraph('• <b>Ringkasan Saldo:</b> Dashboard utama menampilkan total aset gabungan, saldo rekening harian (Checking), saldo tabungan berbunga (Savings), serta nomor rekening unik Anda.', bullet_style))
    story.append(Paragraph('• <b>Riwayat Transaksi Real-Time:</b> Tabel mutasi menampilkan seluruh riwayat kredit dan debit secara kronologis, lengkap dengan cap waktu ISO, nama pihak pengirim/penerima, kategori pengeluaran, dan status eksekusi ledger.', bullet_style))

    # Panduan 3: Mengirim Transfer & OTP
    story.append(Paragraph('Langkah 3: Mengirim Uang (Transfer Dana P2P & Antar Bank)', h2_style))
    story.append(Paragraph('1. Buka tab <b>\'Transfer\'</b> pada menu dashboard.', bullet_style))
    story.append(Paragraph('2. Pilih rekening asal pendebetan (misal: Primary Checking Account).', bullet_style))
    story.append(Paragraph('3. Masukkan <b>Nomor Rekening Tujuan</b> (10 digit angka) atau klik salah satu kontak dari daftar <i>Saved Beneficiaries</i>.', bullet_style))
    story.append(Paragraph('4. Masukkan nominal uang yang ingin dikirim dan tambahkan catatan transaksi opsional (contoh: <i>"Pembayaran sewa kantor"</i>).', bullet_style))
    story.append(Paragraph('5. <b>Verifikasi Keamanan OTP:</b> Demi menjamin keamanan anti-pembajakan sesi, sistem akan meminta 6 digit OTP. Masukkan kode verifikasi <code>123456</code> (kode demo resmi sistem). Saldo akan berpindah seketika tanpa jeda.', bullet_style))

    # Panduan 4: Kelola Daftar Penerima
    story.append(Paragraph('Langkah 4: Manajemen Daftar Penerima Tersimpan (Beneficiaries / Payees)', h2_style))
    story.append(Paragraph('• <b>Menambah Kontak Baru:</b> Masuk ke tab <i>\'Beneficiaries\'</i>, klik <i>\'Add Recipient\'</i>, masukkan Nama Panggilan (Nickname), Nomor Rekening 10 digit, dan Nama Bank. Klik Simpan.', bullet_style))
    story.append(Paragraph('• <b>Transfer Cepat 1-Klik:</b> Seluruh penerima tersimpan akan muncul sebagai kartu kontak cepat di formulir transfer sehingga Anda tidak perlu mengetik ulang nomor rekening tujuan.', bullet_style))

    # Panduan 5: Manajemen Kartu & Keamanan Darurat
    story.append(Paragraph('Langkah 5: Kontrol Keamanan Kartu Debit (Card Freeze & Spending Limits)', h2_style))
    story.append(Paragraph('• <b>Fitur Pembekuan Kartu Instan (Card Freeze):</b> Jika kartu Anda tertinggal di merchant, hilang, atau Anda melihat transaksi mencurigakan, segera klik tombol <b>\'Freeze Card\'</b> pada panel kartu debit. Seketika itu juga, semua otorisasi belanja kartu akan ditolak di level core gateway. Dana masuk dan transfer via aplikasi tetap aman berjalan normal.', bullet_style))
    story.append(Paragraph('• <b>Membuka Blokir Kartu (Unfreeze Card):</b> Jika kartu telah ditemukan kembali, cukup klik tombol <b>\'Unfreeze Card\'</b> untuk mengaktifkan kembali kartu dalam hitungan detik.', bullet_style))
    story.append(Paragraph('• <b>Atur Limit Pengeluaran Harian:</b> Anda dapat menggeser slider limit belanja harian (dari $100 hingga $25,000 per hari) untuk membatasi risiko kerugian akibat skimming atau pencurian kartu.', bullet_style))

    # Panduan 6: Simulasi Pinjaman & KPR
    story.append(Paragraph('Langkah 6: Kalkulator Finansial & Simulasi Pinjaman (Loan Calculator)', h2_style))
    story.append(Paragraph('• <b>Simulasi Kredit & KPR:</b> Gunakan tab <i>\'Calculators\'</i> untuk merencanakan pembiayaan pribadi, kredit kendaraan, atau KPR hunian.', bullet_style))
    story.append(Paragraph('• <b>Parameter Perhitungan:</b> Masukkan nominal pokok pinjaman (Principal), pilih tenor pengembalian (12 s/d 60 bulan), dan tentukan estimasi suku bunga tahunan (APR). Sistem secara otomatis menghitung estimasi angsuran bulanan pokok + bunga dengan formula amortisasi baku.', bullet_style))

    # Panduan 7: Kalkulator Valuta Asing (Forex)
    story.append(Paragraph('Langkah 7: Konversi Valas & Kurs Real-Time (Forex Calculator)', h2_style))
    story.append(Paragraph('• <b>Konversi Multi-Mata Uang:</b> Sistem mendukung perhitungan nilai tukar interbank langsung antara USD, EUR, GBP, JPY, SGD, AUD, CAD, dan IDR.', bullet_style))
    story.append(Paragraph('• <b>Transparansi Biaya Spread:</b> Nilai konversi ditampilkan transparan beserta persentase selisih kurs beli-jual (spread margin) dan estimasi biaya konversi dalam denominasi USD.', bullet_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # BAB 3: FITUR LENGKAP CHAT AI & CARA MENGGUNAKANNYA (DETAILED AI CAPABILITIES)
    # =========================================================================
    story.append(Paragraph('3. Eksplorasi Fitur Lengkap Tirenn AI Copilot & Panduan Penggunaan', h1_style))
    story.append(Paragraph(
        'Tirenn AI Copilot adalah asisten kecerdasan buatan otonom dengan kapabilitas <b>Tool Calling Langsung</b> '
        'ke buku besar (Core Banking Ledger) dan pencarian semantik vektor (ChromaDB Vector RAG). Asisten ini beroperasi '
        'menggunakan arsitektur <i>Multi-Agent Swarm</i> yang terdiri dari 5 Sub-Agent spesialis.', body_style
    ))

    # Tabel Sub-Agent & Domain
    story.append(Paragraph('Arsitektur Domain & Sub-Agent Tirenn AI:', h2_style))
    ai_agent_data = [
        [Paragraph('Sub-Agent Name', th_style), Paragraph('Domain Tanggung Jawab', th_style), Paragraph('MCP Tools yang Dijalankan', th_style), Paragraph('Tipe Output Interaktif', th_style)],
        [Paragraph('<b>TransactionSubAgent</b>', tc_style), Paragraph('Operasi perbankan, mutasi, saldo & transfer P2P', tc_style), Paragraph('<code>get_balance</code>, <code>execute_transfer</code>, <code>get_recent_transactions</code>', tc_style), Paragraph('Kartu Konfirmasi Transfer (Interactive OTP Card)', tc_style)],
        [Paragraph('<b>SecuritySubAgent</b>', tc_style), Paragraph('Kontrol proteksi kartu, pemblokiran & limit belanja', tc_style), Paragraph('<code>freeze_card</code>, <code>unfreeze_card</code>, <code>set_spending_limit</code>', tc_style), Paragraph('Kartu Status Proteksi & Slider Limit Rekening', tc_style)],
        [Paragraph('<b>WealthSubAgent</b>', tc_style), Paragraph('Kalkulator valas, simulasi pinjaman/KPR & kontak penerima', tc_style), Paragraph('<code>calculate_forex</code>, <code>calculate_loan</code>, <code>list_beneficiaries</code>', tc_style), Paragraph('Kartu Konversi Valas, Skedul Amortisasi Kredit', tc_style)],
        [Paragraph('<b>IdentitySubAgent</b>', tc_style), Paragraph('Pemeriksaan profil nasabah & level kepatuhan KYC', tc_style), Paragraph('<code>get_user_profile</code>, <code>get_kyc_status</code>', tc_style), Paragraph('Kartu Identitas Digital & Lencana Verifikasi', tc_style)],
        [Paragraph('<b>SupportFaqSubAgent</b>', tc_style), Paragraph('Pencarian semantik kebijakan, biaya & SOP perbankan', tc_style), Paragraph('<code>search_bank_faq</code> (ChromaDB Hybrid Vector Search)', tc_style), Paragraph('Jawaban Naratif Markdown dengan Rujukan Regulasi', tc_style)],
    ]
    t_ai_agent = Table(ai_agent_data, colWidths=[105, 125, 140, 134])
    t_ai_agent.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_ai_agent)
    story.append(Spacer(1, 6))

    story.append(Paragraph('Daftar Fitur Chat AI & Cara Menggunakannya Langkah-demi-Langkah:', h2_style))

    # Fitur 1
    story.append(Paragraph('<b>Fitur 1: Pengecekan Saldo & Portofolio Akun Real-Time</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Memeriksa saldo terkini pada Primary Checking Account maupun High-Yield Savings tanpa perlu menavigasi menu dashboard.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Buka widget chat AI, lalu ketikkan perintah dalam bahasa santai atau formal.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Berapa sisa saldo rekening saya sekarang?"</code> atau <code>"Check my account balance"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI memanggil tool <code>get_balance</code>, memverifikasi token JWT nasabah, dan menampilkan saldo riil akun beserta nomor rekening terpotong.', bullet_style))

    # Fitur 2
    story.append(Paragraph('<b>Fitur 2: Riwayat Mutasi Transaksi & Rincian Pengeluaran (Spending Breakdown)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Menginspeksi riwayat transaksi terakhir dan mengagregasi total pengeluaran per kategori (Makanan, Tagihan, Belanja, Hiburan).', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Mintalah ringkasan aktivitas keuangan atau riwayat debit/kredit terbaru.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Tampilkan 5 transaksi terakhir saya"</code> atau <code>"Rincikan pengeluaran saya bulan ini"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI memanggil <code>get_recent_transactions</code> atau <code>get_spending_breakdown</code> dan menyajikannya dalam tabel ringkas beserta grafik persentase kategori.', bullet_style))

    # Fitur 3
    story.append(Paragraph('<b>Fitur 3: Eksekusi Pengiriman Uang Otomatis (Smart P2P Transfer & OTP Confirmation)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Menyiapkan dan mengeksekusi transfer dana ke rekening nasabah lain dengan pengawasan otentikasi aman <i>Human-in-the-Loop</i>.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Berikan instruksi transfer lengkap dengan nominal uang dan nomor rekening/nama penerima.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Kirim $50 ke rekening 1000000002 untuk bayar sewa"</code> atau <code>"Transfer 100 dollar ke Sarah Smith"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI memanggil tool <code>execute_transfer</code> dalam mode persiapan dan memunculkan <b>Kartu Konfirmasi Transfer Interaktif</b> di dalam percakapan chat. Masukkan kode OTP <code>123456</code> pada kartu tersebut untuk merilis dana secara seketika.', bullet_style))

    # Fitur 4
    story.append(Paragraph('<b>Fitur 4: Pemblokiran Darurat & Pembukaan Kartu Debit (Instant Freeze / Unfreeze)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Mengamankan kartu debit nasabah dalam hitungan milidetik jika dicurigai hilang atau dibobol pihak tak berwenang.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Ketik perintah pembekuan atau pembukaan blokir secara langsung ke AI.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Bekukan kartu debit saya sekarang, kartu saya tertinggal"</code> atau <code>"Unfreeze my debit card"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI mengeksekusi <code>freeze_card</code> / <code>unfreeze_card</code> dan menampilkan kartu konfirmasi visual bahwa status otorisasi kartu telah berhasil diubah.', bullet_style))

    # Fitur 5
    story.append(Paragraph('<b>Fitur 5: Pengaturan Batas Limit Belanja Harian Kartu (Daily Spending Limit)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Mengontrol batas toleransi debit maksimal kartu dalam 1 hari kalender untuk pencegahan kebocoran dana.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Sebutkan nominal limit belanja baru yang Anda kehendaki.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Ubah limit belanja harian kartu saya jadi $500"</code> atau <code>"Set daily card limit to $2500"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI memanggil <code>set_spending_limit</code> dan mengonfirmasi pembaruan limit kuota transaksi di level core database.', bullet_style))

    # Fitur 6
    story.append(Paragraph('<b>Fitur 6: Simulasi Pinjaman Pribadi, Kredit Kendaraan & KPR (Loan Simulation)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Melakukan kalkulasi amortisasi pembiayaan dengan perhitungan pokok, bunga, dan angsuran bulanan secara presisi.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Berikan parameter jumlah pinjaman, jangka waktu tenor, dan estimasi suku bunga tahunan.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Hitung cicilan pinjaman $20,000 selama 36 bulan dengan bunga 6.5%"</code> atau <code>"Simulasi KPR 150000 USD tenor 10 tahun"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI memanggil <code>calculate_loan</code> dan menyajikan <b>Kartu Simulasi Pembiayaan</b> berisi angsuran per bulan, total bunga yang dibayar, serta jadwal pembayaran.', bullet_style))

    # Fitur 7
    story.append(Paragraph('<b>Fitur 7: Konversi Kurs Valuta Asing Real-Time & Transparansi Biaya (Forex Calculator)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Menghitung nilai tukar valuta asing interbank antara USD, EUR, GBP, JPY, SGD, AUD, CAD, dan IDR beserta biaya spread.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Masukkan pasangan mata uang dan jumlah uang yang ingin dikonversi.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Berapa 500 USD jika ditukar ke EUR?"</code> atau <code>"Konversi 1000 AUD ke USD hari ini"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI memanggil <code>calculate_forex</code> dan memunculkan <b>Kartu Nilai Tukar Valas</b> interaktif dengan kurs interbank terkini dan rincian biaya spread transparan.', bullet_style))

    # Fitur 8
    story.append(Paragraph('<b>Fitur 8: Manajemen Daftar Kontak Penerima Favorit (Beneficiaries)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Menampilkan dan menambah rekening rekanan yang sering ditransfer langsung lewat percakapan AI.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Tanyakan daftar penerima atau instruksikan penyimpanan kontak baru.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Tampilkan daftar penerima tersimpan saya"</code> atau <code>"Simpan rekening 1000000003 atas nama Diana Prince di bank Tirenn"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI memanggil <code>list_beneficiaries</code> atau <code>add_beneficiary</code> dan merender kartu daftar kontak penerima tersimpan.', bullet_style))

    # Fitur 9
    story.append(Paragraph('<b>Fitur 9: Pemeriksaan Profil Nasabah & Status Kepatuhan KYC (Identity Status)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Memeriksa kelengkapan berkas identitas, nomor telepon terdaftar, serta level verifikasi KYC akun (Tier 1, Tier 2, atau Tier 3).', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Tanyakan status profil akun atau kepatuhan data nasabah Anda.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Tampilkan status KYC dan data profil saya"</code> atau <code>"Apakah akun saya sudah lolos verifikasi Tier 2?"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI memanggil <code>get_user_profile</code> dan <code>get_kyc_status</code> lalu menyajikan ringkasan identitas terverifikasi.', bullet_style))

    # Fitur 10
    story.append(Paragraph('<b>Fitur 10: Tanya Jawab Regulasi, Biaya & Kebijakan Bank (Vector RAG Knowledge Search)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Menjawab pertanyaan seputar kebijakan perbankan, tabel biaya wire, suku bunga tabungan, dan SOP operasional bank tanpa halusinasi.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Ajukan pertanyaan bebas seputar aturan atau prosedur bank.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Berapa biaya transfer wire internasional?"</code> atau <code>"Bagaimana aturan penalti pencairan deposito sebelum jatuh tempo?"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> AI memanggil <code>search_bank_faq</code> ke database vektor ChromaDB dan menyajikan kutipan jawaban resmi yang akurat sesuai dokumen manual ini.', bullet_style))

    # Fitur 11
    story.append(Paragraph('<b>Fitur 11: Eksekusi Perintah Majemuk Bertahap (Chained Multi-Step DAG Orchestration)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Kemampuan unik Tirenn AI untuk memecah instruksi kompleks menjadi serangkaian aksi berantai secara otomatis.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Gabungkan dua atau lebih instruksi dalam satu kalimat pesan chat.', bullet_style))
    story.append(Paragraph('<i>Contoh Perintah Chat:</i> <code>"Cek kurs 250 USD ke EUR, lalu siapkan transfer uang tersebut ke rekening 1000000002 untuk Sarah"</code>.', ai_prompt_style))
    story.append(Paragraph('• <b>Hasil Kerja AI:</b> Planner Orchestrator membuat Directed Acyclic Graph (DAG): Step 1 memanggil <code>WealthSubAgent</code> untuk konversi kurs -> hasil nominal diteruskan ke Step 2 memanggil <code>TransactionSubAgent</code> untuk menyiapkan transfer.', bullet_style))

    # Fitur 12
    story.append(Paragraph('<b>Fitur 12: Manajemen Sesi Percakapan & Tombol Reset (Clear Context)</b>', body_style))
    story.append(Paragraph('• <b>Fungsi:</b> Menghapus memori konteks obrolan sementara di cache Redis agar Anda dapat memulai topik baru tanpa terpengaruh pembicaraan lama.', bullet_style))
    story.append(Paragraph('• <b>Cara Menggunakan:</b> Klik ikon tombol <b>Reset Session</b> (ikon panah melingkar) di bilah navigasi chat AI Copilot sebelah tombol tutup (X). Riwayat konteks obrolan akan langsung disegarkan seketika.', bullet_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # BAB 4: DIREKTORI LENGKAP FREQUENTLY ASKED QUESTIONS (FAQ)
    # =========================================================================
    story.append(Paragraph('4. Direktori Resmi Tanya Jawab Nasabah (Knowledge Base FAQ)', h1_style))
    story.append(Paragraph(
        'Berikut adalah kumpulan pertanyaan yang paling sering diajukan oleh nasabah Tirenn Core Banking '
        'beserta jawaban resmi dan solusi teknisnya. Informasi di bawah ini juga diindeks ke dalam basis '
        'vektor RAG Tirenn AI:', body_style
    ))

    # Kategori A: Akun & Keamanan
    story.append(Paragraph('Kategori A: Akun, Verifikasi & Keamanan Akses', h2_style))
    faqs_a = [
        ('Q1: Apa saja syarat membuka rekening perbankan di Tirenn Bank?',
         'Jawab: Syarat utama pembukaan rekening adalah memiliki identitas resmi yang sah (KTP untuk WNI atau Paspor untuk WNA), alamat email aktif, nomor telepon seluler yang dapat menerima SMS/OTP, serta setoran awal minimal $10.00 untuk rekening Checking.'),
        
        ('Q2: Apakah dana simpanan saya di Tirenn Bank aman dan terjamin?',
         'Jawab: Ya, sangat aman. Seluruh simpanan nasabah dijamin oleh regulasi penjaminan simpanan perbankan hingga $250,000 per nasabah. Selain itu, basis data kami dilindungi enkripsi AES-256 tingkat militer untuk data diam (at-rest) dan TLS 1.3 untuk transmisi jaringan.'),
        
        ('Q3: Bagaimana jika saya lupa kata sandi akun saya?',
         'Jawab: Anda dapat mengklik tombol "Forgot Password" pada modal login. Sistem akan mengirimkan tautan reset kata sandi terenkripsi ke alamat email terdaftar Anda dengan masa berlaku 15 menit. Anda juga dapat meminta bantuan tim Customer Support jika email tidak dapat diakses.'),
        
        ('Q4: Bisakah saya memiliki beberapa jenis rekening berbeda di bawah 1 akun?',
         'Jawab: Ya. Setiap nasabah terverifikasi secara otomatis mendapatkan Primary Checking Account dan dapat membuka rekening High-Yield Savings atau Deposito Berjangka (CD) langsung melalui tombol "Open Account" di dashboard tanpa perlu verifikasi ulang.'),
        
        ('Q5: Berapa lama sesi login saya aktif sebelum otomatis keluar (logout)?',
         'Jawab: Demi keamanan akun Anda dari akses pihak ketiga yang tidak berwenang, sesi login berbasis token JWT akan kedaluwarsa secara otomatis setelah 24 jam tidak aktif, atau segera setelah Anda mengklik tombol "Sign Out" di navigasi atas.')
    ]
    for q, a in faqs_a:
        story.append(Paragraph(f'<b>{q}</b>', faq_q_style))
        story.append(Paragraph(a, faq_a_style))

    # Kategori B: Transfer & Pembayaran
    story.append(Paragraph('Kategori B: Transfer Dana, Biaya Layanan & Batas Transaksi', h2_style))
    faqs_b = [
        ('Q6: Berapa biaya transfer dana ke sesama rekening Tirenn Bank?',
         'Jawab: Biaya transfer sesama rekening Tirenn Bank (P2P Internal) adalah <b>$0.00 alias GRATIS sepenuhnya</b> tanpa batasan frekuensi transaksi per hari.'),
        
        ('Q7: Mengapa transaksi transfer uang saya selalu meminta kode OTP?',
         'Jawab: Kode One-Time Password (OTP) adalah lapisan otentikasi lapis dua (2-Factor Authentication) wajib untuk mencegah eksekusi transaksi ilegal jika perangkat Anda ditinggalkan dalam keadaan login. Masukkan kode demo resmi <b>123456</b> untuk memvalidasi pemindahan dana.'),
        
        ('Q8: Berapa batas (limit) maksimal pengiriman uang harian saya?',
         'Jawab: Batas transfer internal P2P harian adalah sebesar $50,000.00 per hari kalender. Untuk transfer domestik antar bank mitra adalah $25,000.00 per hari, dan transfer valas internasional adalah $10,000.00 per hari. Limit akan di-reset setiap pukul 00:00 UTC.'),
        
        ('Q9: Apakah transaksi transfer yang sudah berhasil dapat dibatalkan (recall)?',
         'Jawab: Karena sistem pembukuan Core Banking Tirenn berjalan seketika (sub-detik real-time ledger), transaksi transfer yang telah berstatus "SUCCESS" tidak dapat ditarik kembali secara otomatis. Jika terjadi salah kirim, segera hubungi tim kepatuhan kami dengan menyertakan Nomor Referensi Transaksi.'),
        
        ('Q10: Bagaimana cara menyimpan rekening rekanan agar tidak perlu mengetik ulang?',
         'Jawab: Anda dapat memanfaatkan menu "Beneficiaries" di dashboard atau mencentang opsi "Save as Beneficiary" saat melakukan pengiriman dana. Kontak yang tersimpan akan langsung tersedia dalam daftar pilihan cepat transfer 1-klik.')
    ]
    for q, a in faqs_b:
        story.append(Paragraph(f'<b>{q}</b>', faq_q_style))
        story.append(Paragraph(a, faq_a_style))

    # Kategori C: Kartu & Keamanan
    story.append(Paragraph('Kategori C: Kartu Debit, Pemblokiran Darurat & Limit Belanja', h2_style))
    faqs_c = [
        ('Q11: Apa yang harus segera saya lakukan jika kartu debit saya hilang?',
         'Jawab: Segera buka aplikasi Tirenn Bank dan klik tombol <b>"Freeze Card"</b> pada widget kartu, atau buka Tirenn AI Copilot dan ketik <i>"Freeze my card"</i>. Kartu akan diblokir seketika sehingga tidak ada transaksi belanja yang bisa lolos.'),
        
        ('Q12: Jika kartu saya dalam status "FROZEN", apakah saya tetap bisa menerima transferan?',
         'Jawab: Ya. Status "Card Freeze" hanya menonaktifkan otorisasi kartu debit keluar (transaksi POS, gesek, belanja online, dan tarik tunai ATM). Nomor rekening perbankan Anda tetap berstatus aktif penuh untuk menerima transfer masuk, bunga, maupun dividen.'),
        
        ('Q13: Bagaimana cara mengubah batas maksimal belanja harian kartu debit?',
         'Jawab: Anda dapat mengatur limit belanja kartu kapan saja melalui slider limit di menu kartu atau meminta bantuan AI Copilot (contoh: <i>"Set daily card spending limit to $500"</i>). Pengaturan ini efektif seketika tanpa perlu persetujuan kantor cabang.'),
        
        ('Q14: Apakah kartu debit Tirenn dapat digunakan untuk transaksi belanja di luar negeri?',
         'Jawab: Ya, kartu debit Tirenn mendukung jaringan pembayaran internasional Visa/Mastercard dan dapat digunakan untuk transaksi daring mancanegara serta mesin ATM luar negeri dengan konversi kurs interbank kompetitif.')
    ]
    for q, a in faqs_c:
        story.append(Paragraph(f'<b>{q}</b>', faq_q_style))
        story.append(Paragraph(a, faq_a_style))

    # Kategori D: Bunga, Tabungan & Pinjaman
    story.append(Paragraph('Kategori D: Suku Bunga Tabungan, Deposito & Pinjaman', h2_style))
    faqs_d = [
        ('Q15: Bagaimana skema penghitungan bunga tabungan High-Yield Savings (4.25% APY)?',
         'Jawab: Suku bunga High-Yield Savings dihitung berdasarkan saldo harian efektif pada pukul 23:59:59 dengan rumus <i>(Saldo Harian x 4.25%) / 365</i>, dan diakumulasikan lalu dikreditkan ke saldo tabungan Anda pada hari kerja pertama setiap awal bulan kalender.'),
        
        ('Q16: Apakah ada biaya pinalti jika saya mencairkan Deposito (CD) sebelum jatuh tempo?',
         'Jawab: Untuk simpanan Deposito Berjangka (Certificate of Deposit), penarikan dana sebelum tanggal jatuh tempo (early break) dikenakan penyesuaian pinalti sebesar bunga berjalan selama 3 bulan terakhir. Pokok simpanan awal Anda tetap aman dan dikembalikan utuh 100%.'),
        
        ('Q17: Bagaimana cara mengajukan simulasi pinjaman dana atau kredit rumah (KPR)?',
         'Jawab: Buka menu "Calculators" pada antarmuka web, pilih opsi pinjaman yang diinginkan, masukkan jumlah pinjaman dan jangka waktu angsuran. Sistem akan memperlihatkan simulasi skedul amortisasi bulanan, rasio kemampuan bayar, dan total bunga selama tenor pinjaman.')
    ]
    for q, a in faqs_d:
        story.append(Paragraph(f'<b>{q}</b>', faq_q_style))
        story.append(Paragraph(a, faq_a_style))

    # Kategori E: Asisten AI Copilot
    story.append(Paragraph('Kategori E: Asisten Keuangan Pintar Tirenn AI Copilot', h2_style))
    faqs_e = [
        ('Q18: Apakah Tirenn AI Copilot bisa melakukan transfer uang tanpa konfirmasi saya?',
         'Jawab: TIDAK PERNAH. Tirenn AI menerapkan arsitektur keamanan Human-in-the-Loop. Asisten hanya akan merangkum instruksi transfer dan memunculkan kartu konfirmasi pembayaran di layar. Dana tidak akan berkurang sebelum Anda secara sadar memasukkan kode OTP 6 digit.'),
        
        ('Q19: Bagaimana asisten AI dapat mengetahui aturan kebijakan bank secara akurat?',
         'Jawab: Asisten AI Tirenn terintegrasi langsung dengan database vektor ChromaDB melalui teknik RAG (Retrieval-Augmented Generation). Setiap kali Anda mengajukan pertanyaan mengenai biaya atau kebijakan, sistem mengambil kutipan langsung dari manual resmi ini sehingga terbebas dari halusinasi.'),
        
        ('Q20: Bagaimana cara mereset atau membersihkan riwayat obrolan AI?',
         'Jawab: Anda dapat mengklik tombol ikon putar ulang (Reset Session) di bagian atas bilah judul chat asisten AI. Tindakan ini akan menghapus jejak konteks percakapan sementara di Redis dan menyegarkan sesi interaksi Anda dari awal.'),
        
        ('Q21: Apakah percakapan saya dengan Tirenn AI dijamin kerahasiaannya?',
         'Jawab: Ya. Semua prompt dan jawaban dienkripsi, dikaitkan secara ketat dengan ID pengguna yang sah melalui otentikasi JWT Bearer, dan tidak pernah dibagikan kepada pihak ketiga atau digunakan untuk melatih model publik.')
    ]
    for q, a in faqs_e:
        story.append(Paragraph(f'<b>{q}</b>', faq_q_style))
        story.append(Paragraph(a, faq_a_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # BAB 5: PUSAT BANTUAN & KONTAK RESMI TIRENN
    # =========================================================================
    story.append(Paragraph('5. Layanan Pelanggan & Saluran Kontak Darurat Resmi', h1_style))
    story.append(Paragraph(
        'Jika Anda mengalami kendala teknis darurat, kendala kegagalan transfer, atau menduga adanya aktivitas '
        'penipuan pada akun Anda, tim layanan pelanggan Tirenn siap membantu Anda 24 jam sehari, 7 hari seminggu:', body_style
    ))

    contact_data = [
        [Paragraph('Kanal Layanan', th_style), Paragraph('Detail Kontak Resmi', th_style), Paragraph('Waktu Layanan', th_style), Paragraph('Keterangan / Fungsi', th_style)],
        [Paragraph('<b>Tirenn 24/7 Hotline</b>', tc_style), Paragraph('<b>+1 (800) 555-TIRENN</b> / (021) 5088-BANK', tc_style), Paragraph('24 Jam / 7 Hari', tc_style), Paragraph('Bantuan darurat pemblokiran akun, kartu hilang, fraud alert', tc_style)],
        [Paragraph('<b>Email Dukungan Nasabah</b>', tc_style), Paragraph('<code>support@tirenn.bank</code>', tc_style), Paragraph('Maksimal respons 2 jam', tc_style), Paragraph('Kendala teknis akun, pertanyaan mutasi, verifikasi KYC', tc_style)],
        [Paragraph('<b>Unit Kepatuhan & Fraud</b>', tc_style), Paragraph('<code>compliance@tirenn.bank</code>', tc_style), Paragraph('Hari kerja 08:00 - 18:00', tc_style), Paragraph('Laporan investigasi sengketa transaksi dan pelaporan AML', tc_style)],
        [Paragraph('<b>Kantor Pusat Operasional</b>', tc_style), Paragraph('Tirenn Financial Tower, Level 28, Sudirman Financial District', tc_style), Paragraph('Senin - Jumat (09:00 - 16:00)', tc_style), Paragraph('Layanan nasabah korporat dan konsultasi investasi', tc_style)],
    ]
    t_contact = Table(contact_data, colWidths=[110, 160, 95, 139])
    t_contact.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_contact)
    story.append(Spacer(1, 10))

    closing_notice = (
        '<b>PEMBERITAHUAN HUKUM:</b> Panduan ini diterbitkan oleh Tirenn Core Banking Corporation sebagai manual '
        'operasional resmi nasabah dan rujukan pengetahuan kecerdasan buatan. Seluruh suku bunga, biaya layanan, dan '
        'ketentuan operasional tunduk pada peraturan perundang-undangan perbankan digital yang berlaku. Hak Cipta © 2026 '
        'Tirenn Banking Corp. Seluruh hak cipta dilindungi undang-undang.'
    )
    t_closing = Table([[Paragraph(closing_notice, callout_style)]], colWidths=[504])
    t_closing.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_closing)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f'[SUCCESS] Generated manual PDF successfully at: {output_path}')


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'tirenn_bank_system_manual.pdf'
    create_manual(target)
