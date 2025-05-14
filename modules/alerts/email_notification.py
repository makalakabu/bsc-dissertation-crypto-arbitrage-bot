import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import asdict
from crypto_arbitrage_bot.config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER

def email_alert(opportunity):
    """
    Sends an email alert with details of the best arbitrage opportunity using Yahoo SMTP.
    """
    subject = f"Arbitrage Opportunity: {opportunity.asset_pair} | Profit {opportunity.net_profit_percentage:.2f}%"

    # Format the message body
    data = asdict(opportunity)
    body_lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            body_lines.append(f"\n{key.upper()}:")
            for sub_key, sub_value in value.items():
                body_lines.append(f"  - {sub_key}: {sub_value}")
        else:
            body_lines.append(f"{key}: {value}")
    body = "\n".join(body_lines)

    # Construct the email
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.mail.yahoo.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email alert sent successfully via Yahoo.")
    except Exception as e:
        print(f" Failed to send email via Yahoo: {e}")
