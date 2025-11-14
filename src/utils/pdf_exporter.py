from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def _remove_disclaimer(markdown_text: str) -> str:
    """Remove the disclaimer section starting from the heading.

    This removes lines from the first occurrence of "### ⚠️ 免责声明" to the end.
    """
    marker = "### ⚠️ 免责声明"
    if marker not in markdown_text:
        return markdown_text
    return markdown_text.split(marker)[0].rstrip() + "\n"


def _sanitize_for_pdf(text: str) -> str:
    """Sanitize text to avoid garbled characters in PDF.

    - Remove common emoji icons used in the markdown template
    - Replace some special symbols with simpler equivalents
    - Drop characters outside the BMP range
    """
    replacements = {
        "🧍": "",
        "🩸": "",
        "🚽": "",
        "🖥️": "",
        "❤️": "",
        "⚠️": "",
        "◆": "",
        "■": "",
        "●": "",
        "○": "",
        "•": "",
        "▪": "",
        "◦": "",
        "▶": "",
        "►": "",
        "▸": "",
        "▹": "",
        "◾": "",
        "◼": "",
        "★": "",
        "☆": "",
        "**": "",
        # 上标数字替换为普通数字
        "²": "2",
        "³": "3",
        "⁴": "4",
        "⁵": "5",
        "⁶": "6",
        "⁷": "7",
        "⁸": "8",
        "⁹": "9",
        # 微符号替换为字母 u，避免 µmol/L 等单位乱码
        "µ": "u",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)

    # Remove non-BMP characters that the font may not support
    text = "".join(ch for ch in text if ord(ch) <= 0xFFFF)
    return text


def create_analysis_pdf(markdown_text: str) -> bytes:
    """Create a PDF bytes object from the AI analysis markdown.

    The generated PDF will NOT include the disclaimer section and will be
    sanitized to reduce乱码 caused by不支持的字符。
    """
    cleaned_text = _sanitize_for_pdf(_remove_disclaimer(markdown_text))

    # 注册支持中文的字体，避免导出PDF时出现乱码
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    base = styles["Normal"]
    base.fontName = "STSong-Light"
    base.leading = 16

    heading = ParagraphStyle(
        "Heading",
        parent=base,
        fontSize=16,
        leading=20,
        spaceBefore=8,
        spaceAfter=4,
        bold=True,
    )

    subheading = ParagraphStyle(
        "Subheading",
        parent=base,
        fontSize=14,
        leading=18,
        spaceBefore=6,
        spaceAfter=2,
    )

    story = []
    lines = cleaned_text.split("\n")
    for raw in lines:
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue

        # 一级标题（例如 ### 体检报告诊断结果）
        if line.startswith("### "):
            title = line[4:].strip()
            story.append(Paragraph(title, heading))
            continue

        # 二级标题（如 #### 一般检查）
        if line.startswith("#### "):
            title = line[5:].strip()
            story.append(Paragraph(title, subheading))
            continue

        # 列表项 "- 文本" -> "• 文本"
        if line.startswith("- "):
            text = "• " + line[2:].strip()
            story.append(Paragraph(text, base))
            continue

        # 简单处理表格：忽略表头和分隔行，只保留每行数据，用“ | ”连接
        if "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts and not set(parts) <= {":---", "---"}:
                text = "  ".join(parts)
                story.append(Paragraph(text, base))
            continue

        # 其他普通文本
        story.append(Paragraph(raw.replace("  ", "&nbsp;&nbsp;"), base))
        
        story.append(Spacer(1, 4))

    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value
