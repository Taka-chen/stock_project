# -*- coding: utf-8 -*-
"""
PDF generator module.
Exports stock news summaries to PDF with CJK font support.
Auto-detects system CJK fonts on macOS, Windows, and Linux.
"""

import os
import sys
import platform
from datetime import datetime
from pathlib import Path

# ── Font Detection ────────────────────────────────────────────────────────────

def _find_cjk_font() -> str | None:
    """
    Auto-detect a CJK-compatible TrueType/OpenType font on the current system.
    Returns absolute path to font file, or None if not found.
    """
    system = platform.system()

    candidates = []

    if system == "Darwin":  # macOS
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
        ]
    elif system == "Windows":
        candidates = [
            r"C:\Windows\Fonts\msjh.ttc",      # Microsoft JhengHei (Traditional)
            r"C:\Windows\Fonts\msyh.ttc",       # Microsoft YaHei (Simplified)
            r"C:\Windows\Fonts\mingliu.ttc",    # MingLiU
            r"C:\Windows\Fonts\kaiu.ttf",       # DFKai-SB
            r"C:\Windows\Fonts\arial.ttf",
        ]
    else:  # Linux
        linux_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJKtc-Regular.otf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        ]
        candidates = linux_paths

    for path in candidates:
        if os.path.isfile(path):
            return path

    return None


# ── PDF Generator ─────────────────────────────────────────────────────────────

def generate_pdf(
    ticker: str,
    name: str,
    market: str,
    summary_text: str,
    google_articles: list,
    bing_articles: list,
    output_dir: str,
) -> str:
    """
    Generate a PDF report for a stock.
    Returns the path of the saved PDF file.
    Falls back to text-based PDF if CJK font is unavailable.
    """
    try:
        from fpdf import FPDF, XPos, YPos
    except ImportError:
        raise ImportError("fpdf2 not installed. Run: pip install fpdf2")

    font_path = _find_cjk_font()
    has_cjk = font_path is not None

    os.makedirs(output_dir, exist_ok=True)

    # Filename with timestamp
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_ticker = ticker.replace("/", "-").replace("\\", "-")
    filename = f"{safe_ticker}_{ts}.pdf"
    filepath = os.path.join(output_dir, filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Register CJK font if available
    if has_cjk:
        try:
            pdf.add_font("CJK", fname=font_path, uni=True)
            pdf.add_font("CJK", style="B", fname=font_path, uni=True)
            cjk_available = True
        except Exception as e:
            print(f"[PDF] Font load error: {e}")
            cjk_available = False
    else:
        cjk_available = False

    def set_font(size=11, bold=False):
        if cjk_available:
            pdf.set_font("CJK", style="B" if bold else "", size=size)
        else:
            pdf.set_font("Helvetica", style="B" if bold else "", size=size)

    def write_line(text: str, size=10, bold=False, color=(30, 30, 30)):
        set_font(size=size, bold=bold)
        pdf.set_text_color(*color)
        if not cjk_available:
            # Encode to ASCII-safe for non-CJK fallback
            text = text.encode("ascii", errors="replace").decode("ascii")
        pdf.multi_cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def write_divider():
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

    # ── Header ──
    market_label = "台股" if market == "TW" else "美股"
    pdf.set_fill_color(30, 58, 138)  # navy
    pdf.rect(0, 0, pdf.w, 28, "F")
    set_font(size=16, bold=True)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(8)
    header_text = f"股票新聞分析報告 — {name} ({ticker}) {market_label}"
    if not cjk_available:
        header_text = header_text.encode("ascii", errors="replace").decode("ascii")
    pdf.cell(0, 10, header_text, align="C")
    pdf.ln(6)

    date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    set_font(size=9)
    date_line = f"產生時間：{date_str}"
    if not cjk_available:
        date_line = date_line.encode("ascii", errors="replace").decode("ascii")
    pdf.cell(0, 5, date_line, align="C")
    pdf.ln(10)

    if not cjk_available:
        write_line(
            "[Note] CJK font not found. Chinese characters replaced with '?'. "
            "Install a CJK font for full support.",
            size=8, color=(180, 0, 0)
        )
        pdf.ln(2)

    # ── Claude Summary ──
    write_line("📋 Claude AI 整理摘要", size=13, bold=True, color=(30, 58, 138))
    write_divider()
    pdf.ln(1)

    if summary_text:
        for line in summary_text.split("\n"):
            stripped = line.strip()
            if not stripped:
                pdf.ln(2)
                continue
            is_heading = stripped.startswith("##") or stripped.startswith("##")
            if stripped.startswith("## "):
                write_line(stripped[3:], size=11, bold=True, color=(30, 58, 138))
            elif stripped.startswith("- ") or stripped.startswith("• "):
                pdf.set_x(pdf.l_margin + 5)
                write_line(stripped, size=9, color=(50, 50, 50))
            else:
                write_line(stripped, size=9, color=(50, 50, 50))
    else:
        write_line("（尚未填入 Claude 摘要）", size=9, color=(150, 150, 150))

    pdf.ln(5)

    # ── Google News ──
    write_line("🔍 Google 新聞", size=13, bold=True, color=(30, 58, 138))
    write_divider()
    _write_articles(pdf, google_articles, cjk_available, write_line)

    # ── Bing News ──
    write_line("🌐 Bing 新聞", size=13, bold=True, color=(30, 58, 138))
    write_divider()
    _write_articles(pdf, bing_articles, cjk_available, write_line)

    # ── Disclaimer ──
    pdf.ln(5)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(pdf.l_margin, pdf.get_y(), pdf.w - pdf.l_margin - pdf.r_margin, 12, "F")
    write_line(
        "⚠️ 免責聲明：本報告內容僅供參考，不構成任何投資建議。投資有風險，請自行評估。",
        size=8, color=(120, 120, 120)
    )

    pdf.output(filepath)
    return filepath


def _write_articles(pdf, articles: list, cjk_available: bool, write_line):
    """Write article list to PDF."""
    if not articles:
        write_line("（無新聞資料）", size=9, color=(150, 150, 150))
        pdf.ln(3)
        return

    from fpdf import XPos, YPos

    for i, article in enumerate(articles[:6], 1):
        title = article.get("title", "")
        source = article.get("source", "")
        published = article.get("published", "")
        summary = article.get("summary", "")

        # Article number + title
        write_line(f"{i}. {title}", size=9, bold=True, color=(20, 20, 80))

        meta_parts = []
        if source:
            meta_parts.append(source)
        if published:
            meta_parts.append(published)
        if meta_parts:
            write_line("   " + " | ".join(meta_parts), size=8, color=(120, 120, 120))

        if summary:
            write_line(f"   {summary[:180]}", size=8, color=(80, 80, 80))

        pdf.ln(2)

    pdf.ln(4)
