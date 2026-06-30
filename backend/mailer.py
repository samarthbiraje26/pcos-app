"""
Email helpers for transactional account emails.
"""
import smtplib
from email.message import EmailMessage
from flask import current_app


def mail_is_configured():
    config = current_app.config
    return bool(config.get("MAIL_ENABLED") and config.get("MAIL_SERVER") and config.get("MAIL_FROM"))


def send_email(to_email, subject, text_body):
    if not mail_is_configured():
        current_app.logger.warning("Email skipped because mail settings are incomplete or disabled.")
        return False

    config = current_app.config
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config["MAIL_FROM"]
    message["To"] = to_email
    message.set_content(text_body)

    smtp_class = smtplib.SMTP_SSL if config.get("MAIL_USE_SSL") else smtplib.SMTP

    try:
        with smtp_class(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=20) as server:
            if not config.get("MAIL_USE_SSL") and config.get("MAIL_USE_TLS"):
                server.starttls()
            if config.get("MAIL_USERNAME"):
                server.login(config["MAIL_USERNAME"], config.get("MAIL_PASSWORD", ""))
            server.send_message(message)
        return True
    except Exception:
        current_app.logger.exception("Failed to send email to %s", to_email)
        return False


def send_welcome_email(user):
    dashboard_url = f"{current_app.config['FRONTEND_BASE_URL'].rstrip('/')}/dashboard.html"
    text_body = (
        f"Hi {user.name},\n\n"
        "Welcome to PCOS Detect.\n\n"
        "Your account has been created successfully. You can sign in and access your dashboard here:\n"
        f"{dashboard_url}\n\n"
        "If you did not create this account, please contact support.\n\n"
        "PCOS Detect"
    )
    return send_email(user.email, "Welcome to PCOS Detect", text_body)


def send_password_reset_email(user, reset_url):
    text_body = (
        f"Hi {user.name},\n\n"
        "We received a request to reset your PCOS Detect password.\n\n"
        "Use the link below to set a new password:\n"
        f"{reset_url}\n\n"
        f"This link will expire in {current_app.config['RESET_TOKEN_EXPIRES_MINUTES']} minutes and can only be used once.\n\n"
        "If you did not request a password reset, you can safely ignore this email.\n\n"
        "PCOS Detect"
    )
    return send_email(user.email, "Reset your PCOS Detect password", text_body)
