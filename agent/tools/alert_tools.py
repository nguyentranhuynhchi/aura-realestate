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
    if subject.startswith(f"[{status}]") or subject.startswith("["):
        msg["Subject"] = f"{subject} - {os.getenv('HOSTNAME', 'Docker')}"
    else:
        msg["Subject"] = f"[{status}] {subject} - {os.getenv('HOSTNAME', 'Docker')}"

    sync_note = ""
    if diff_code and status == "SUCCESS":
        sync_note = """
    <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 14px; margin-top: 15px; border-radius: 6px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <p style="margin: 0; color: #1e40af; font-weight: bold; font-size: 15px;">📢 1. ĐỒNG BỘ MÃ NGUỒN (CODE UPDATE):</p>
        <p style="margin: 6px 0 8px 0; color: #1e3a8a; font-size: 13px;">Coder Agent đã tạo bản vá tối ưu hơn trong thư mục <code>agent/sandbox/update_code/</code>. Kho <code>baseline/</code> vẫn được giữ nguyên an toàn. Nếu muốn cập nhật code này làm chuẩn mốc mới, bạn chạy lệnh PowerShell sau:</p>
        <pre style="background: #1e293b; color: #f8fafc; padding: 10px 12px; border-radius: 4px; font-size: 12.5px; overflow-x: auto; margin: 0; font-family: Consolas, 'Courier New', monospace;">Copy-Item -Path "agent\\sandbox\\update_code\\*" -Destination "agent\\sandbox\\baseline\\" -Recurse -Force</pre>
    </div>
    """

    deploy_note = ""
    if status == "SUCCESS":
        deploy_note = """
    <div style="background: #fefce8; border-left: 4px solid #ca8a04; padding: 14px; margin-top: 15px; border-radius: 6px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <p style="margin: 0; color: #854d0e; font-weight: bold; font-size: 15px;">🛡️ 2. QUY TRÌNH PHÊ DUYỆT DEPLOY MÔ HÌNH (HUMAN-IN-THE-LOOP):</p>
        <p style="margin: 6px 0 8px 0; color: #713f12; font-size: 13px;">Mô hình mới <b>KHÔNG</b> tự động ghi đè lên Production Backend mà được lưu an toàn tại <code>model_registry/</code> chờ quyết định của bạn.</p>
        
        <p style="margin: 10px 0 4px 0; font-weight: bold; color: #854d0e; font-size: 13px;">👉 Bước 1: Xem danh sách so găng các phiên bản mô hình:</p>
        <pre style="background: #1e293b; color: #f8fafc; padding: 8px 12px; border-radius: 4px; font-size: 12.5px; margin: 0 0 8px 0; font-family: Consolas, 'Courier New', monospace;">python -m agent.tools.deploy_model --list</pre>

        <p style="margin: 8px 0 4px 0; font-weight: bold; color: #854d0e; font-size: 13px;">👉 Bước 2: Phê duyệt Deploy phiên bản mới nhất lên Production Backend (Tự động Backup mô hình cũ):</p>
        <pre style="background: #1e293b; color: #38bdf8; padding: 8px 12px; border-radius: 4px; font-size: 12.5px; margin: 0 0 6px 0; font-family: Consolas, 'Courier New', monospace;">python -m agent.tools.deploy_model --latest</pre>
        <p style="margin: 0 0 10px 0; color: #713f12; font-size: 12px;"><i>(Lệnh chạy trong Docker container: <code>docker exec -it aura_agent_service python -m agent.tools.deploy_model --latest -y</code>)</i></p>

        <p style="margin: 8px 0 4px 0; font-weight: bold; color: #854d0e; font-size: 13px;">👉 Bước 3: Hoàn tác về mô hình cũ ngay lập tức nếu cần (Rollback Safety):</p>
        <pre style="background: #1e293b; color: #f87171; padding: 8px 12px; border-radius: 4px; font-size: 12.5px; margin: 0; font-family: Consolas, 'Courier New', monospace;">python -m agent.tools.deploy_model --rollback</pre>
    </div>
    """

    body_html = f"""
    <h3>HỆ THỐNG MULTI-AGENT MLOPS TỰ HÀNH - BÁO CÁO VẬN HÀNH</h3>
    <p><b>Trạng thái:</b> <span style="color: {'#16a34a' if status == 'SUCCESS' else ('#d97706' if status == 'DEGRADED' else '#dc2626')}; font-weight: bold;">{status}</span></p>
    <p><b>Chẩn đoán của Supervisor:</b></p>
    <blockquote style="background: #f8f9fa; border-left: 4px solid {'#16a34a' if status == 'SUCCESS' else ('#d97706' if status == 'DEGRADED' else '#dc2626')}; padding: 10px;">
        {diagnosis.replace(chr(10), '<br>')}
    </blockquote>
{sync_note}
{deploy_note}
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