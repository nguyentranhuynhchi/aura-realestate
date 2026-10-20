# agent/tools/pdf_report_generator.py
import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_audit_pdf_report(state: dict, output_path: str = "/tmp/mlops_audit_report.pdf") -> str:
    """
    Biên soạn báo cáo PDF thẩm định MLOps nhiều chương:
    - Bìa & Executive Summary
    - Chi tiết từng vòng lặp: Metadata 22 micro-modules, Chẩn đoán Supervisor, Bản vá Git Diff
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
        parent=styles['Heading1'], 
        fontSize=20, 
        leading=24, 
        textColor=colors.HexColor("#1A365D"), 
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'ChapterH2', 
        parent=styles['Heading2'], 
        fontSize=13, 
        leading=16, 
        textColor=colors.HexColor("#2B6CB0"), 
        spaceBefore=14, 
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody', 
        parent=styles['Normal'], 
        fontSize=9, 
        leading=13, 
        textColor=colors.HexColor("#2D3748")
    )
    callout_style = ParagraphStyle(
        'Callout', 
        parent=styles['Normal'], 
        fontSize=9, 
        leading=12, 
        textColor=colors.HexColor("#742A2A"), 
        backColor=colors.HexColor("#FFF5F5"), 
        borderPadding=6
    )

    elements = []

    # 1. TIÊU ĐỀ BÁO CÁO & MỐC THỜI GIAN
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph("AURA REAL ESTATE - MLOPS AUTONOMOUS AUDIT REPORT", title_style))
    elements.append(Paragraph(f"<b>Thời điểm tạo báo cáo:</b> {now_str} | <b>Hệ thống:</b> Multi-Agent StateGraph (Airflow + LangGraph)", body_style))
    elements.append(Spacer(1, 12))

    # 2. BẢNG TỔNG KẾT EXECUTIVE SUMMARY
    dag_status = state.get("dag_status", "UNKNOWN").upper()
    iter_count = state.get("iteration_count", 1)
    metrics = state.get("model_metrics") or {}
    r2_val = metrics.get("R2_score", "N/A")
    mae_val = metrics.get("MAE", "N/A")
    status_label = "HOÀN THÀNH XUẤT SẮC" if dag_status == "SUCCESS" else "CẦN KỸ SƯ XEM XÉT"

    summary_table_data = [
        ["Thông số hệ thống", "Kết quả thẩm định", "Ghi chú vận hành"],
        ["Trạng thái Airflow DAG", dag_status, status_label],
        ["Tổng số vòng thử nghiệm", f"{iter_count} vòng", "Cầu dao an toàn: Max 3 vòng"],
        ["Điểm giải thích phương sai (R2)", str(r2_val), "Chuẩn tối thiểu: >= 0.65"],
        ["Sai số tuyệt đối (MAE)", f"{mae_val} Tỷ VNĐ" if mae_val != "N/A" else "N/A", "Sai lệch giá nhà trung bình"],
    ]

    t_summary = Table(summary_table_data, colWidths=[150, 180, 190])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 15))

    # 3. CHƯƠNG CHI TIẾT: THẨM ĐỊNH METADATA 22 MICRO-MODULES
    elements.append(Paragraph("CHƯƠNG 1: THẨM ĐỊNH METADATA 22 MICRO-MODULES", h2_style))
    pipeline_summary = state.get("pipeline_summary") or {}
    steps = pipeline_summary.get("steps", {})

    meta_table_data = [["Giai đoạn Pipeline", "Module kiểm tra", "Chỉ số Metadata trích xuất"]]
    
    # Bóc tách metadata các khâu chính
    c_info = steps.get("1_crawler", {})
    meta_table_data.append(["1_Crawler", "03_raw_extractor.py", f"Bản ghi cào mới: {c_info.get('raw_records', 0)}"])
    
    eda_skew = steps.get("2_eda", {}).get("skew_analysis", {})
    meta_table_data.append(["2_EDA", "03_distribution_skew.py", f"Đề xuất: {eda_skew.get('recommendation', 'N/A')}"])
    
    p_dedup = steps.get("3_preprocessing", {}).get("deduplicator", {})
    meta_table_data.append(["3_Preprocessing", "07_deduplicator.py", f"Dữ liệu sạch: {p_dedup.get('total_clean_records', 0)} dòng"])
    
    split_info = steps.get("5_split", {}).get("splitter", {})
    meta_table_data.append(["5_Split", "01_data_splitter.py", f"Train: {split_info.get('train_rows', 0)} | Val: {split_info.get('val_rows', 0)} | Test: {split_info.get('test_rows', 0)}"])
    
    m_info = steps.get("6_modeling", {}).get("final_evaluation", {})
    meta_table_data.append(["6_Modeling", "05_evaluate_champion.py", f"R2: {m_info.get('R2_score', 'N/A')} | Status: {m_info.get('status', 'N/A')}"])

    t_meta = Table(meta_table_data, colWidths=[110, 160, 250])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4A5568")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 15))

    # 4. CHƯƠNG CHI TIẾT: PHÂN TÍCH CỦA SUPERVISOR AGENT
    elements.append(Paragraph("CHƯƠNG 2: CHẨN ĐOÁN CỦA AUTONOMOUS SUPERVISOR", h2_style))
    diagnosis_text = state.get("diagnosis", "Không có chẩn đoán chi tiết.")
    elements.append(Paragraph(f"<b>Ý kiến chuyên môn:</b> {diagnosis_text}", callout_style))
    elements.append(Spacer(1, 15))

    # 5. CHƯƠNG CHI TIẾT: BẢN VÁ GIT DIFF DO CODER AGENT SINH RA
    diff_text = state.get("code_diff", "")
    if diff_text:
        elements.append(Paragraph("CHƯƠNG 3: BẢN VÁ MÃ NGUỒN (GIT DIFF CODE PATCH)", h2_style))
        elements.append(Paragraph("Coder Agent đã tự động hiệu chỉnh mã nguồn trong Sandbox (Xanh: Dòng mới, Đỏ: Dòng cũ):", body_style))
        elements.append(Spacer(1, 6))
        # Giới hạn 40 dòng diff để vừa trang in
        diff_snippet = "\n".join(diff_text.strip().splitlines()[:40])
        elements.append(Preformatted(diff_snippet, ParagraphStyle('DiffCode', fontName='Courier', fontSize=7, leading=9, textColor=colors.HexColor("#2C5282"))))

    # Xuất file PDF
    doc.build(elements)
    return output_path