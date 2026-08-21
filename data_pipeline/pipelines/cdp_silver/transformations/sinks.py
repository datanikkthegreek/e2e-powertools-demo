"""Pipeline sinks: send transactional emails per silver-event row.

Self-contained: the GmailDataSource lives in this file so the streaming
pipeline doesn't depend on cross-file load order or a sibling helper
module — same pattern as the working notebook
(`data_pipeline/notebooks/send_mail_create_account.ipynb`). Keep this
in sync with that notebook and with `data_pipeline/scripts/send_gmail.py`
if any of the email logic changes.

Two sinks are defined here, both driven by the same GmailDataSource:

- `welcome_email_sink`  — one email per `event_sign_up` row
                          (subject/body come from `event_sign_up.py`).
- `purchase_email_sink` — one email per `event_purchase` row
                          (subject/body come from `event_purchase.py`).
"""

import mimetypes
import os
import smtplib
import sys
import hashlib
from email.message import EmailMessage
from typing import Iterable, Optional

from pyspark import pipelines as dp
from pyspark import cloudpickle as _pyspark_cloudpickle
from pyspark.sql.datasource import (
    DataSource,
    DataSourceStreamWriter,
    WriterCommitMessage,
)
from pyspark.sql.types import StructType


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
    """Send an email through a Gmail account via SMTPS.

    Prefer reading `gmail_address` and `app_password` from Databricks secrets
    (`dbutils.secrets.get(...)`). For Gmail, use an App Password (2-Step
    Verification must be enabled on the account).
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

            print(
                {
                    "partition_id": partition_id,
                    "recipient": str(recipient),
                    "subject": str(subject),
                    "body_sha256": hashlib.sha256(
                        str(body_text).encode("utf-8")
                    ).hexdigest()[:16],
                }
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


# DLT exec()s this file under a mangled module name (NOT __main__), so
# cloudpickle would pickle GmailDataSource by reference and executor
# Python workers would fail to import that mangled module. Registering
# this module by value ships the class bytecode along with each task —
# same effect the notebook gets for free because notebook code lives in
# __main__.
#
# PySpark vendors its own cloudpickle (`pyspark.cloudpickle`), so we must
# register against THAT instance — the top-level `import cloudpickle` has
# separate module-level state that Spark's serializer doesn't consult.
_pyspark_cloudpickle.register_pickle_by_value(sys.modules[__name__])

# Register the custom Spark Python data source so `format="gmail"` below
# resolves. Runs once per pipeline restart.
spark.dataSource.register(GmailDataSource)

_GMAIL_ADDRESS = "nikolaos.servos@gmail.com"
_GMAIL_PASSWORD = dbutils.secrets.get(scope="cdp_demo", key="gmail_app_password")

_EMAIL_OPTIONS = {
    "gmailAddress":       _GMAIL_ADDRESS,
    "appPassword":        _GMAIL_PASSWORD,
    "targetRecipientCol": "email",
    "subjectCol":         "subject",
    "bodyCol":            "body",
}

dp.create_sink(name="welcome_email_sink",  format="gmail", options=_EMAIL_OPTIONS)
dp.create_sink(name="purchase_email_sink", format="gmail", options=_EMAIL_OPTIONS)


# Use `dp.read_stream(name)` (not `spark.readStream.table(name)`) so the
# pipeline analyzer resolves the reference by short name — same key the pipeline
# uses when registering the streaming table via `@dp.table(name="…")`. Going
# through `spark.readStream.table` would let Spark expand the short name to
# the pipeline's default `catalog.schema.table` FQN, and the per-pipeline
# dataset registry doesn't index by FQN, so the read fails with
# UnresolvedDatasetException even though the table is right there.
@dp.append_flow(name="welcome_email_flow", target="welcome_email_sink")
def welcome_email_flow():
    return (
        dp.read_stream("event_sign_up")
           .select("email", "subject", "body")
    )


@dp.append_flow(name="purchase_email_flow", target="purchase_email_sink")
def purchase_email_flow():
    return (
        dp.read_stream("event_purchase")
           .select("email", "subject", "body")
    )
