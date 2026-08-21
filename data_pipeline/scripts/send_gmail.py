from email.message import EmailMessage
import mimetypes
import os
import smtplib
from typing import Iterable, Optional


def send_gmail_email(
    to_addresses,
    subject: str,
    body_text: str,
    *,
    gmail_address: Optional[str] = None,
    app_password: Optional[str] = None,
    cc_addresses: Optional[Iterable[str]] = None,
    bcc_addresses: Optional[Iterable[str]] = None,
    body_html: Optional[str] = None,
    attachment_paths: Optional[Iterable[str]] = None,
):
    """
    Send an email through a Gmail account from a Databricks notebook.

    Recommended usage in Databricks:
      * Store the Gmail address and Gmail App Password in a secret scope.
      * Pass them in with dbutils.secrets.get(...).

    Notes:
      * For Gmail, use an App Password rather than your normal account password.
      * The Gmail account usually needs 2-Step Verification enabled.
    """

    if isinstance(to_addresses, str):
        to_addresses = [to_addresses]
    else:
        to_addresses = list(to_addresses)

    cc_addresses = [] if cc_addresses is None else list(cc_addresses)
    bcc_addresses = [] if bcc_addresses is None else list(bcc_addresses)
    attachment_paths = [] if attachment_paths is None else list(attachment_paths)

    if not to_addresses:
        raise ValueError("Provide at least one recipient in to_addresses.")

    if not gmail_address:
        raise ValueError(
            "gmail_address is required. Prefer reading it from Databricks secrets."
        )

    if not app_password:
        raise ValueError(
            "app_password is required. For Gmail, use a Gmail App Password."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = gmail_address
    message["To"] = ", ".join(to_addresses)

    if cc_addresses:
        message["Cc"] = ", ".join(cc_addresses)

    message.set_content(body_text)

    if body_html:
        message.add_alternative(body_html, subtype="html")

    for path in attachment_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Attachment not found: {path}")

        mime_type, _ = mimetypes.guess_type(path)
        if mime_type:
            maintype, subtype = mime_type.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"

        with open(path, "rb") as f:
            message.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(path),
            )

    all_recipients = to_addresses + cc_addresses + bcc_addresses

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, app_password)
        smtp.send_message(message, to_addrs=all_recipients)

    return {
        "status": "sent",
        "from": gmail_address,
        "to": to_addresses,
        "cc": cc_addresses,
        "bcc_count": len(bcc_addresses),
        "attachment_count": len(attachment_paths),
        "subject": subject,
    }


from pyspark.sql.datasource import DataSource, DataSourceStreamWriter, WriterCommitMessage
from pyspark.sql.types import StructType


class EmailWriterCommitMessage(WriterCommitMessage):
    def __init__(self, partition_id: int, sent_count: int):
        self.partition_id = partition_id
        self.sent_count = sent_count


class GmailStreamWriter(DataSourceStreamWriter):
    def __init__(self, options):
        self.options = options
        self.gmail_address = self.options.get("gmailAddress")
        self.app_password = self.options.get("appPassword")
        self.target_recipient_col = self.options.get("targetRecipientCol")
        self.subject_col = self.options.get("subjectCol")
        self.body_col = self.options.get("bodyCol")

        if not self.gmail_address:
            raise ValueError("The option 'gmailAddress' is required.")
        if not self.app_password:
            raise ValueError("The option 'appPassword' is required.")
        if not self.target_recipient_col:
            raise ValueError("The option 'targetRecipientCol' is required.")
        if not self.subject_col:
            raise ValueError("The option 'subjectCol' is required.")
        if not self.body_col:
            raise ValueError("The option 'bodyCol' is required.")

    def write(self, iterator):
        from pyspark import TaskContext

        context = TaskContext.get()
        partition_id = context.partitionId() if context else 0
        sent_count = 0

        for row in iterator:
            row_dict = row.asDict(recursive=True)
            recipient = row_dict.get(self.target_recipient_col)
            subject = row_dict.get(self.subject_col)
            body_text = row_dict.get(self.body_col)

            if recipient is None:
                raise ValueError(
                    f"Column '{self.target_recipient_col}' is missing or null in an input row."
                )
            if subject is None:
                raise ValueError(
                    f"Column '{self.subject_col}' is missing or null in an input row."
                )
            if body_text is None:
                raise ValueError(
                    f"Column '{self.body_col}' is missing or null in an input row."
                )

            send_gmail_email(
                to_addresses=str(recipient),
                subject=str(subject),
                body_text=str(body_text),
                gmail_address=self.gmail_address,
                app_password=self.app_password,
            )
            sent_count += 1

        return EmailWriterCommitMessage(partition_id=partition_id, sent_count=sent_count)

    def commit(self, messages, batchId) -> None:
        total_sent = sum(message.sent_count for message in messages)
        print(
            {
                "batch_id": batchId,
                "partitions": len(messages),
                "emails_sent": total_sent,
            }
        )

    def abort(self, messages, batchId) -> None:
        total_sent = sum(message.sent_count for message in messages)
        print(
            {
                "batch_id": batchId,
                "status": "aborted",
                "emails_sent_before_abort": total_sent,
            }
        )


class GmailDataSource(DataSource):
    @classmethod
    def name(cls):
        return "gmail"

    def schema(self):
        return "ID long, target_recipient_col string, subject_col string, body_col string"

    def streamWriter(self, schema: StructType, overwrite: bool):
        return GmailStreamWriter(self.options)