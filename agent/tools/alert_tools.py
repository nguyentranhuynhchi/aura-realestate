import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
try:
    from langchain_core.tools import tool
except ImportError:
    def tool(func):
        func.invoke = lambda kwargs: func(**kwargs)
        return func
from typing import Optional

@tool
def send_email_alert(subject: str, diagnosis: str, diff_code: Optional[str] = "", status: str = "ACTION_REQUIRED", pdf_path: Optional[str] = None) -> str:
    """Gửi email báo cáo kèm file đính kèm PDF thẩm định tự hành."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("ALERT_RECIPIENT", "nguyentranhuynhchi@gmail.com")

    if not smtp_user or not smtp_pass:
        return json.dumps({"status": "skipped", "reason": "Chưa cấu hình SMTP_USER hoặc SMTP_PASSWORD."})

    msg = MIMEMultipart()
    msg["From"] = f"Aura MLOps Agent <{smtp_user}>"
    msg["To"] = recipient
    msg["Subject"] = f"[{status}] {subject} - {os.getenv('HOSTNAME', 'Docker')}"

    body_html = f"""
    <h3>HỆ THỐNG MULTI-AGENT MLOPS TỰ HÀNH - BÁO CÁO VẬN HÀNH</h3>
    <p><b>Trạng thái:</b> <span style="color: {'green' if status == 'SUCCESS' else 'red'}; font-weight: bold;">{status}</span></p>
    <p><b>Chẩn đoán của Supervisor:</b></p>
    <blockquote style="background: #f8f9fa; border-left: 4px solid #007bff; padding: 10px;">
        {diagnosis.replace(chr(10), '<br>')}
    </blockquote>
    <p><i>Bản báo cáo thẩm định chi tiết định dạng PDF đã được đính kèm vào email này.</i></p>
    """
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    # ĐÍNH KÈM FILE PDF NẾU TỒN TẠI
    if pdf_path and os.path.exists(pdf_path):
        try:
            with open(pdf_path, "rb") as f_pdf:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f_pdf.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_path)}")
            msg.attach(part)
        except Exception as e:
            print(f"[CẢNH BÁO] Không đính kèm được PDF: {e}")

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return json.dumps({"status": "email_sent", "recipient": recipient, "pdf_attached": bool(pdf_path)})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})