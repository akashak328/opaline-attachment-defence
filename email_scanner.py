"""
email_scanner.py
────────────────
Real-time IMAP inbox monitor:
  1. Connects to Gmail via IMAP SSL
  2. Fetches unseen emails
  3. Extracts attachments (.txt / .docx / .pdf)
  4. Scans attachment content for malicious keywords
  5. If malicious → converts to PNG → deletes original mail → sends alert
  6. Logs all actions to MySQL (read_data table)
"""

import email
import imaplib
import os
import mysql.connector

from attachment_converter import (
    text_to_image,
    word_to_img,
    pdf_to_img,
    scan_txt_for_keywords,
    scan_docx_for_keywords,
    scan_pdf_for_keywords,
)

ATTACHMENTS_DIR = "static/attachments"

# ── DB connection (reuse app-level connection or create new) ──────────────────
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    charset="utf8",
    database="malicious_email"
)


def sendmail(usermail: str, mess1: str, maxid: int, n1: int):
    """
    Sends an alert email to the user.
    Import from app.py in production to reuse Flask-Mail context.
    Stub kept here for module independence.
    """
    print(f"[ALERT] Sending mail to {usermail}: {mess1}")


# ── Core IMAP Scanner ─────────────────────────────────────────────────────────

def emailsink(usermail: str, pwd: str, uname: str, max_mails: int = 3):
    """
    Connect to Gmail IMAP, scan unseen emails, and process attachments.

    Args:
        usermail  : Gmail address configured by the user
        pwd       : Gmail app password
        uname     : system username (for DB logging)
        max_mails : max number of emails to process per scan cycle
    """
    mycursor = mydb.cursor()

    # ── Connect ──────────────────────────────────────────────────────────────
    mail       = imaplib.IMAP4_SSL('imap.gmail.com')
    retcode, _ = mail.login(usermail, pwd)
    if retcode != 'OK':
        print("[ERROR] IMAP login failed.")
        return

    mail.select('inbox')
    retcode, messages = mail.search(None, '(UnSeen)')
    if retcode != 'OK':
        print("[ERROR] Could not fetch unseen messages.")
        return

    n = 0
    for num in messages[0].split():
        if n >= max_mails:
            break

        n += 1
        mycursor.execute("SELECT max(id)+1 FROM read_data")
        maxid = mycursor.fetchone()[0] or 1

        typ, data = mail.fetch(num, '(RFC822)')
        for response_part in data:
            if not isinstance(response_part, tuple):
                continue

            raw_email        = data[0][1]
            raw_email_string = raw_email.decode('utf-8')
            email_message    = email.message_from_string(raw_email_string)
            original         = email.message_from_bytes(response_part[1])

            ff = ""
            fu = "0"

            for part in email_message.walk():
                # Skip multipart containers
                if part.get_content_maintype() == 'multipart':
                    fu = "1"
                    continue

                # Skip inline content with no disposition
                if part.get('Content-Disposition') is None:
                    continue

                if fu != "1":
                    continue

                fileName = part.get_filename()
                if not fileName:
                    continue

                f1 = fileName.split(".")
                if len(f1) < 2 or f1[1] not in ("txt", "docx", "pdf"):
                    continue

                # ── Save attachment ───────────────────────────────────────────
                fname = f"f{maxid}_{fileName}"
                ff   += fname + "|"
                fpath = os.path.join(ATTACHMENTS_DIR, fname)
                with open(fpath, 'wb') as fp:
                    fp.write(part.get_payload(decode=True))
                print(f"[INFO] Attachment saved: {fpath}")

                subj   = original['Subject']
                sender = original['From']
                ext    = f1[1]

                # ── Scan & convert if malicious ───────────────────────────────
                is_malicious = False
                n1           = 0

                if ext == "txt":
                    is_malicious = scan_txt_for_keywords(fname)
                    if is_malicious:
                        text_to_image(fname, maxid)
                        n1 = 1

                elif ext == "docx":
                    is_malicious = scan_docx_for_keywords(fname)
                    if is_malicious:
                        nn = word_to_img(fname, maxid)
                        n1 = nn - 1

                elif ext == "pdf":
                    is_malicious = scan_pdf_for_keywords(fname, maxid)
                    if is_malicious:
                        n1 = pdf_to_img(fname, maxid)

                # ── Take action if malicious ──────────────────────────────────
                if is_malicious:
                    # Delete original mail from inbox
                    mail.store(num, '+FLAGS', r'(\Deleted)')
                    mess1 = "Malicious mail has been detected and deleted ***"
                    sendmail(usermail, mess1, maxid, n1)
                    print(f"[WARN] Malicious attachment detected: {fname}. Mail deleted.")

                    # Log to DB
                    sql = """INSERT INTO read_data
                             (id, subject, sender, uname, message, spam_st, filename, img_count)
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                    val = (maxid, subj, sender, uname, '', '0', fname, n1)
                    mycursor.execute(sql, val)
                    mydb.commit()
                    print(f"[INFO] DB record inserted: id={maxid}")

    mail.expunge()
    mail.close()
    mail.logout()
    print("[INFO] IMAP scan complete.")
