# agent/tools/pdf_report_generator.py
import os
import json
import unicodedata
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ------------------------------------------------------------------------------
# 1. ĐĂNG KÝ FONT UNICODE TIẾNG VIỆT (TỰ ĐỘNG PHÁT HIỆN FONT TRONG CONTAINER & HOST)
# ------------------------------------------------------------------------------
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

def setup_unicode_font():
    global FONT_REGULAR, FONT_BOLD
    font_search_paths = [
        os.path.join(os.path.dirname(__file__), "..", "resources", "fonts", "Arial.ttf"),
        "/app/agent/resources/fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    bold_search_paths = [
        os.path.join(os.path.dirname(__file__), "..", "resources", "fonts", "Arial-Bold.ttf"),
        "/app/agent/resources/fonts/Arial-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    f_path = next((p for p in font_search_paths if os.path.exists(p)), None)
    b_path = next((p for p in bold_search_paths if os.path.exists(p)), None)

    if f_path:
        try:
            pdfmetrics.registerFont(TTFont("VN-Font", f_path))
            FONT_REGULAR = "VN-Font"
            if b_path:
                pdfmetrics.registerFont(TTFont("VN-Font-Bold", b_path))
                FONT_BOLD = "VN-Font-Bold"
            else:
                FONT_BOLD = "VN-Font"
        except Exception:
            FONT_REGULAR = "Helvetica"
            FONT_BOLD = "Helvetica-Bold"

setup_unicode_font()


def sanitize_text(text: str) -> str:
    """Nếu không có font Unicode tiếng Việt, chuyển sang không dấu để tránh ô vuông đen ■."""
    if not text:
        return ""
    if FONT_REGULAR == "Helvetica":
        nfkd = unicodedata.normalize('NFKD', str(text))
        return "".join([c for c in nfkd if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D')
    return str(text)


def generate_audit_pdf_report(state: dict, output_path: str = "/tmp/mlops_audit_report.pdf") -> str:
    """
    Biên soạn báo cáo PDF thẩm định MLOps chuyên nghiệp:
    - Bìa & Executive Summary (Minh bạch trạng thái Thành công / Cảnh báo Fallback)
    - Metadata 22 micro-modules (Đọc đầy đủ chỉ số từ State hoặc Fallback)
    - Chẩn đoán chi tiết của Autonomous Supervisor
    - Bản vá Git Unified Diff (nếu có)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=letter, 
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', 
        fontName=FONT_BOLD,
        fontSize=18, 
        leading=22, 
        textColor=colors.HexColor("#1A365D"), 
        spaceAfter=8
    )
    h2_style = ParagraphStyle(
        'ChapterH2', 
        fontName=FONT_BOLD,
        fontSize=12, 
        leading=16, 
        textColor=colors.HexColor("#2B6CB0"), 
        spaceBefore=14, 
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody', 
        fontName=FONT_REGULAR,
        fontSize=9, 
        leading=13, 
        textColor=colors.HexColor("#2D3748")
    )
    callout_style = ParagraphStyle(
        'Callout', 
        fontName=FONT_REGULAR,
        fontSize=9, 
        leading=13, 
        textColor=colors.HexColor("#742A2A"), 
        backColor=colors.HexColor("#FFF5F5"), 
        borderPadding=6
    )
    warning_banner_style = ParagraphStyle(
        'WarnBanner',
        fontName=FONT_BOLD,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#744210"),
        backColor=colors.HexColor("#FEFCBF"),
        borderPadding=6
    )

    elements = []

    # 1. TIÊU ĐỀ BÁO CÁO & MỐC THỜI GIAN
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(sanitize_text("AURA REAL ESTATE - MLOPS AUTONOMOUS AUDIT REPORT"), title_style))
    elements.append(Paragraph(
        sanitize_text(f"<b>Thời điểm tạo báo cáo:</b> {now_str} | <b>Hệ thống:</b> Multi-Agent StateGraph (Airflow + LangGraph)"), 
        body_style
    ))
    elements.append(Spacer(1, 10))

    # Cờ trạng thái
    dag_status = state.get("dag_status", "UNKNOWN").upper()
    is_fallback = state.get("is_fallback", False)
    iter_count = state.get("iteration_count", 0)

    # Nếu đang chạy chế độ phòng vệ Fallback, hiển thị Banner cảnh báo màu vàng
    if is_fallback or dag_status == "DEGRADED":
        elements.append(Paragraph(
            sanitize_text("⚠️ <b>[CẢNH BÁO VẬN HÀNH]:</b> Airflow Webserver gặp sự cố mất kết nối / Timeout. "
            "Toàn bộ số liệu dưới đây được trích xuất từ bản lưu đệm (Snapshot) gần nhất trên đĩa cứng."),
            warning_banner_style
        ))
        elements.append(Spacer(1, 10))

    # 2. BẢNG TỔNG KẾT EXECUTIVE SUMMARY
    metrics = state.get("model_metrics") or {}
    r2_val = metrics.get("r2") if metrics.get("r2") is not None else metrics.get("R2_score", "N/A")
    mae_val = metrics.get("mae") if metrics.get("mae") is not None else metrics.get("MAE", "N/A")

    if is_fallback or dag_status == "DEGRADED":
        status_label = "CẢNH BÁO: DÙNG DỮ LIỆU ĐỆM"
        status_color = colors.HexColor("#DD6B20")
    elif dag_status == "SUCCESS" and state.get("human_approved"):
        status_label = "HOÀN THÀNH XUẤT SẮC"
        status_color = colors.HexColor("#2B6CB0")
    else:
        status_label = "CẦN KỸ SƯ XEM XÉT"
        status_color = colors.HexColor("#E53E3E")

    summary_table_data = [
        [sanitize_text("Thông số hệ thống"), sanitize_text("Kết quả thẩm định"), sanitize_text("Ghi chú vận hành")],
        [sanitize_text("Trạng thái Pipeline"), sanitize_text(dag_status), sanitize_text(status_label)],
        [sanitize_text("Tổng số vòng thử nghiệm"), sanitize_text(f"{iter_count} vòng"), sanitize_text("Cầu dao an toàn: Max 3 vòng")],
        [sanitize_text("Điểm giải thích phương sai (R2)"), sanitize_text(str(r2_val)), sanitize_text("Chuẩn tối thiểu: >= 0.65")],
        [sanitize_text("Sai số tuyệt đối (MAE)"), sanitize_text(f"{mae_val} Tỷ VNĐ" if mae_val != "N/A" else "N/A"), sanitize_text("Sai lệch giá nhà trung bình")],
    ]

    t_summary = Table(summary_table_data, colWidths=[150, 180, 190])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), status_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 15))

    # 3. CHƯƠNG CHI TIẾT: THẨM ĐỊNH METADATA 22 MICRO-MODULES
    elements.append(Paragraph(sanitize_text("CHƯƠNG 1: THẨM ĐỊNH METADATA 22 MICRO-MODULES"), h2_style))
    pipeline_summary = state.get("pipeline_summary") or {}
    steps = pipeline_summary.get("steps", {})

    meta_table_data = [[sanitize_text("Giai đoạn Pipeline"), sanitize_text("Module kiểm tra"), sanitize_text("Chỉ số Metadata trích xuất")]]
    
    # Bóc tách metadata các khâu chính
    c_info = steps.get("1_crawler", {})
    raw_count = c_info.get("raw_records", 0)
    meta_table_data.append([sanitize_text("1_Crawler"), sanitize_text("03_raw_extractor.py"), sanitize_text(f"Bản ghi cào mới: {raw_count}")])
    
    eda_skew = steps.get("2_eda", {}).get("skew_analysis", {})
    skew_rec = eda_skew.get("recommendation", "N/A")
    meta_table_data.append([sanitize_text("2_EDA"), sanitize_text("03_distribution_skew.py"), sanitize_text(f"Đề xuất: {skew_rec}")])
    
    p_dedup = steps.get("3_preprocessing", {}).get("deduplicator", {})
    clean_count = p_dedup.get("total_clean_records", 0)
    meta_table_data.append([sanitize_text("3_Preprocessing"), sanitize_text("07_deduplicator.py"), sanitize_text(f"Dữ liệu sạch: {clean_count} dòng")])
    
    split_info = steps.get("5_split", {}).get("splitter", {})
    train_r = split_info.get("train_rows", 0)
    val_r = split_info.get("val_rows", 0)
    test_r = split_info.get("test_rows", 0)
    meta_table_data.append([sanitize_text("5_Split"), sanitize_text("01_data_splitter.py"), sanitize_text(f"Train: {train_r} | Val: {val_r} | Test: {test_r}")])
    
    m_info = steps.get("6_modeling", {}).get("final_evaluation", {})
    m_r2 = m_info.get("R2_score") or r2_val
    m_status = m_info.get("status", "Challenger")
    meta_table_data.append([sanitize_text("6_Modeling"), sanitize_text("05_evaluate_champion.py"), sanitize_text(f"R2: {m_r2} | Trạng thái: {m_status}")])

    t_meta = Table(meta_table_data, colWidths=[110, 160, 250])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4A5568")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 15))

    # 4. CHƯƠNG CHI TIẾT: PHÂN TÍCH CỦA SUPERVISOR AGENT
    elements.append(Paragraph(sanitize_text("CHƯƠNG 2: CHẨN ĐOÁN CỦA AUTONOMOUS SUPERVISOR"), h2_style))
    diagnosis_text = (
        state.get("supervisor_diagnosis") 
        or state.get("diagnosis") 
        or (state.get("messages", [{}])[-1].get("content") if state.get("messages") else "Không có chẩn đoán chi tiết.")
    )
    elements.append(Paragraph(sanitize_text(f"<b>Ý kiến chuyên môn:</b><br/>{diagnosis_text.replace(chr(10), '<br/>')}"), callout_style))
    elements.append(Spacer(1, 15))

    # 5. CHƯƠNG CHI TIẾT: BẢN VÁ GIT DIFF DO CODER AGENT SINH RA
    diff_text = state.get("diff") or state.get("code_diff", "")
    if diff_text:
        elements.append(Paragraph(sanitize_text("CHƯƠNG 3: BẢN VÁ MÃ NGUỒN (GIT DIFF CODE PATCH)"), h2_style))
        elements.append(Paragraph(sanitize_text("Coder Agent đã tự động hiệu chỉnh mã nguồn trong Sandbox:"), body_style))
        elements.append(Spacer(1, 6))
        diff_snippet = "\n".join(diff_text.strip().splitlines()[:40])
        elements.append(Preformatted(diff_snippet, ParagraphStyle('DiffCode', fontName='Courier', fontSize=7, leading=9, textColor=colors.HexColor("#2C5282"))))

    # Xuất file PDF
    doc.build(elements)
    return output_path
