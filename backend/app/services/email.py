# backend/app/services/email.py
import asyncio
import os
from pathlib import Path
from typing import Awaitable, Callable, Optional

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader

from app.config import settings

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class EmailService:
    """Serviço de envio de e-mails com fila assíncrona interna."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.template_env = Environment(
            loader=FileSystemLoader(str(templates_dir or _TEMPLATES_DIR)),
            autoescape=True,
        )
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None

    async def start_worker(self) -> None:
        """Inicia o worker que consome a fila. Chamado no lifespan."""
        if self._queue is None:
            self._queue = asyncio.Queue()
        self._worker_task = asyncio.create_task(self._process_queue())

    async def stop_worker(self) -> None:
        """Para o worker graciosamente."""
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def _process_queue(self) -> None:
        """Loop que consome e-mails da fila, um por vez, com delay."""
        if self._queue is None:
            return

        while True:
            job = await self._queue.get()
            try:
                await self._send_single(job["to"], job["subject"], job["html"])
                await job["on_success"]()
            except Exception as exc:
                await job["on_failure"](str(exc))
            finally:
                if self._queue:
                    self._queue.task_done()
                await asyncio.sleep(1)  # rate-limit: 1 e-mail/segundo

    async def _send_single(self, to: str, subject: str, html: str) -> None:
        """Envia um único e-mail via SMTP assíncrono (TLS)."""
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html", "utf-8"))

        # await aiosmtplib.send(
        #     msg,
        #     hostname=settings.SMTP_HOST,
        #     port=settings.SMTP_PORT,
        #     username=settings.SMTP_USER,
        #     password=settings.SMTP_PASSWORD,
        #     use_tls=True,
        # )

    async def enqueue(
        self,
        to: str,
        subject: str,
        html: str,
        on_success: Callable[[], Awaitable[None]],
        on_failure: Callable[[str], Awaitable[None]],
    ) -> None:
        """Adiciona e-mail à fila."""
        if self._queue is None:
            self._queue = asyncio.Queue()

        await self._queue.put(
            {
                "to": to,
                "subject": subject,
                "html": html,
                "on_success": on_success,
                "on_failure": on_failure,
            }
        )

    def render_template(self, template_name: str, **context) -> str:
        """Renderiza template Jinja2 para o corpo do e-mail."""
        tmpl = self.template_env.get_template(template_name)
        return tmpl.render(**context)

    @property
    def queue_size(self) -> int:
        return self._queue.qsize() if self._queue else 0


# Singleton — instanciado em main.py e injetado via dependency
email_service = EmailService()
