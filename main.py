import imaplib
import email
import re
import time
from pyrogram import Client, filters

# ========== BOT CONFIG ==========
API_ID =34792718    # <-- apna api_id
API_HASH = "d12293a48e849ee8feee66aa68e482fb"  # <-- apna api_hash
BOT_TOKEN = "8545901037:AAFg6QQhp_9_tz2NNXp_WXFJnAeHls3jDmk"

# ========== GMAIL CONFIG ==========
GMAIL_EMAIL = "kripasindhug059@gmail.com"
GMAIL_APP_PASSWORD = "nndsoqwcybdbvfxe"

FAM_DOMAIN = "@famapp.in"

# ========== BOT ==========
app = Client(
    "fampay_tracker_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


def clean_body(text: str) -> str:
    lines = []
    for line in text.splitlines():
        l = line.lower()
        if any(x in l for x in [
            "updated balance",
            "call us",
            "support@",
            "best,",
            "disclaimer",
            "otp",
            "confidential",
            "famapp header",
            "hey "
        ]):
            continue
        if line.strip():
            lines.append(line.strip())
    return "\n".join(lines)


def parse_transaction(body: str) -> str | None:
    body_l = body.lower()

    # CREDIT / DEBIT
    if "received" in body_l:
        tx_type = "CREDITED"
    elif "paid" in body_l or "debited" in body_l:
        tx_type = "DEBITED"
    else:
        return None

    # Amount
    amount = re.search(r"₹\s?([\d.]+)", body)
    amount = f"₹{amount.group(1)}" if amount else "₹?"

    # From / To
    sender = re.search(r"from\s+([a-zA-Z ]+)", body, re.I)
    receiver = re.search(r"to\s+([a-zA-Z ]+)", body, re.I)

    party = ""
    if tx_type == "CREDITED" and sender:
        party = f"From: {sender.group(1).strip()}"
    if tx_type == "DEBITED" and receiver:
        party = f"To: {receiver.group(1).strip()}"

    # Transaction ID
    txn = re.search(r"Transaction ID\s*:\s*(\w+)", body)
    txn = txn.group(1) if txn else "N/A"

    # Date
    date = re.search(r"\d{1,2}:\d{2}\s*(AM|PM).*?\d{4}", body)
    date = date.group(0) if date else "N/A"

    clean = clean_body(body)

    message = (
        f"💳 FamPay Transaction ({tx_type})\n\n"
        f"Amount: {amount}\n"
        f"{party}\n\n"
        f"Transaction ID: {txn}\n"
        f"Date: {date}\n\n"
        f"{clean}"
    )

    return message


def check_mail_and_send():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
    mail.select("inbox")

    status, data = mail.search(None, f'(UNSEEN FROM "{FAM_DOMAIN}")')
    mail_ids = data[0].split()

    for num in mail_ids:
        _, msg_data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        text = parse_transaction(body)
        if text:
            app.send_message(chat_id="me", text=text)

    mail.logout()


@app.on_message(filters.command("start"))
async def start(_, m):
    await m.reply("✅ FamPay Tracker Bot is running")


if __name__ == "__main__":
    app.start()
    print("Bot started...")

    while True:
        try:
            check_mail_and_send()
            time.sleep(20)  # 20 sec me check
        except Exception as e:
            print("Error:", e)
            time.sleep(30)
