import os
import html
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

logger = logging.getLogger(__name__)

def build_message(job: dict) -> str:
    org = html.escape(job.get("org_name", "Government Organization"))
    role = html.escape(job.get("role_name", "Technical / General Post"))
    branches = html.escape(job.get("branches", "B.Tech CSE / Any Graduate"))
    app_start = html.escape(job.get("app_start", "Refer Notification"))
    last_date = html.escape(job.get("last_date", "Refer Notification"))
    procedure = html.escape(job.get("selection_procedure", "CBT / Written Test / Interview"))
    fee = html.escape(job.get("app_fee", "As per official notification"))
    link = job.get("app_link", "").strip()
    
    # Today's notification date
    alert_date = datetime.now().strftime("%d/%m/%Y")

    return (
        f"📢 <b>New Job Alert: {org}</b>\n"
        f"📅 <b>Alert Date:</b> {alert_date}\n"
        f"• <b>Post / Role Name:</b> {role}\n"
        f"• <b>Eligible Branches:</b> {branches}\n"
        f"• <b>Key Dates:</b>\n"
        f"  - Application Start: {app_start}\n"
        f"  - Last Date: {last_date}\n"
        f"• <b>Selection Procedure:</b> {procedure}\n"
        f"• <b>Application Fee:</b> {fee}\n"
        f"• <b>Application Link:</b> <a href=\"{link}\">{link}</a>"
    )

def send_telegram_alert(job: dict) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
        return False

    payload = {
        "chat_id": CHAT_ID,
        "text": build_message(job),
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
        data = response.json()
        if not data.get("ok"):
            logger.error(f"Telegram API Error ({data.get('error_code')}): {data.get('description')}")
            return False
        return True
    except requests.RequestException as e:
        logger.error(f"Network error sending Telegram alert: {e}")
        return False