import httpx
import aiosmtplib
from email.message import EmailMessage
from app.config import get_settings

settings = get_settings()


async def send_email(subject: str, body: str) -> None:
    if not settings.smtp_user:
        return
    msg = EmailMessage()
    msg["Subject"] = f"[AntiGravity Shield] {subject}"
    msg["From"] = settings.smtp_from
    msg["To"] = settings.alert_email_to
    msg.set_content(body)
    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True,
    )


async def send_telegram(message: str) -> None:
    if not settings.telegram_bot_token:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json={"chat_id": settings.telegram_chat_id, "text": message, "parse_mode": "HTML"})


async def send_discord(title: str, message: str, severity: str = "info") -> None:
    if not settings.discord_webhook_url:
        return
    colors = {"info": 3447003, "warning": 16776960, "critical": 15158332}
    payload = {"embeds": [{"title": title, "description": message, "color": colors.get(severity, 3447003)}]}
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(settings.discord_webhook_url, json=payload)


async def broadcast_alert(title: str, message: str, severity: str = "info") -> None:
    import asyncio
    tasks = [
        send_email(title, message),
        send_telegram(f"<b>{title}</b>\n{message}"),
        send_discord(title, message, severity),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
