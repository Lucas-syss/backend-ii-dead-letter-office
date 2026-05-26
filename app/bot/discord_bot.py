import asyncio
import io
import os

import discord
import httpx
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000").rstrip("/")
COMMAND_PREFIX = os.getenv("DISCORD_COMMAND_PREFIX", "$")

POLL_MAX_ATTEMPTS = int(os.getenv("DISCORD_REPORT_POLL_ATTEMPTS", "90"))
POLL_DELAY_SECONDS = int(os.getenv("DISCORD_REPORT_POLL_DELAY", "5"))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Discord bot online as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not message.content.startswith(f"{COMMAND_PREFIX}report"):
        return

    raw_error = message.content.replace(f"{COMMAND_PREFIX}report", "", 1).strip()

    if not raw_error:
        await message.reply(
            f"Uso: `{COMMAND_PREFIX}report <erro>`\n"
            f"Exemplo: `{COMMAND_PREFIX}report payment-service 503 timeout ao chamar /payments/charge`"
        )
        return

    await message.reply("📨 Recebi o erro. Vou mandar para o Dead Letter Office...")

    try:
        event_id = await ingest_error(raw_error, message)
    except Exception as exc:
        await message.reply(f"❌ Falhei ao enviar para o backend: `{exc}`")
        return

    await message.reply(
        f"✅ Evento criado: `{event_id}`\n"
        "⏳ CrewAI está a analisar. Vou mandar o report quando acabar."
    )

    try:
        await wait_for_report_and_reply(event_id, message)
    except Exception as exc:
        await message.reply(f"❌ Erro ao procurar o report do evento `{event_id}`: `{exc}`")


async def ingest_error(raw_error: str, message: discord.Message) -> str:
    payload = {
        "source": "api_call",
        "service": "discord-report",
        "error_code": None,
        "error_message": raw_error,
        "payload": {
            "discord_channel_id": str(message.channel.id),
            "discord_message_id": str(message.id),
            "discord_author": str(message.author),
            "content": raw_error,
        },
        "metadata": {
            "reported_from": "discord",
            "guild_id": str(message.guild.id) if message.guild else None,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as http:
            response = await http.post(
                f"{BACKEND_API_URL}/api/v1/events/ingest",
                json=payload,
            )
    except httpx.RequestError as exc:
        raise RuntimeError(f"não consegui contactar o backend em {BACKEND_API_URL}: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text.strip() or response.reason_phrase
        raise RuntimeError(f"{response.status_code}: {detail}")

    data = response.json()
    event_id = data.get("event_id")

    if not event_id:
        raise RuntimeError(f"backend não devolveu event_id: {data}")

    return event_id


async def wait_for_report_and_reply(event_id: str, message: discord.Message):
    async with httpx.AsyncClient(timeout=20.0) as http:
        for attempt in range(1, POLL_MAX_ATTEMPTS + 1):
            await asyncio.sleep(POLL_DELAY_SECONDS)

            try:
                response = await http.get(f"{BACKEND_API_URL}/api/v1/events/{event_id}")
            except httpx.RequestError as exc:
                raise RuntimeError(
                    f"não consegui contactar o backend em {BACKEND_API_URL}: {exc}"
                ) from exc

            if response.status_code == 404:
                continue

            response.raise_for_status()
            data = response.json()

            incident = data.get("incident")

            if incident:
                await send_incident_report(message, data, incident)
                return

            if attempt in {10, 50, 80}:
                await message.channel.send(
                    f"⏳ Ainda estou à espera do report para o evento `{event_id}`..."
                )

    await message.reply(
        f"⚠️ O evento `{event_id}` ainda está sem report no tempo limite do bot.\n"
        "Isto pode acontecer quando o modelo está lento ou com rate limit. "
        "Vê os logs do backend ou consulta o evento mais tarde."
    )


async def send_incident_report(
    message: discord.Message,
    event_data: dict,
    incident: dict,
):
    event_id = event_data.get("event_id") or event_data.get("id") or "unknown"
    report_md = incident.get("report_md") or ""

    if not report_md:
        await message.reply("⚠️ O incident foi criado, mas não tem relatório completo.")
        return

    report_file = discord.File(
        fp=io.BytesIO(report_md.encode("utf-8")),
        filename=f"incident-report-{event_id}.md",
    )

    await message.reply(
        "📎 Relatório completo em anexo.",
        file=report_file,
    )


def truncate(text: str | None, limit: int = 900) -> str:
    if not text:
        return "N/A"

    text = str(text).strip()

    if len(text) <= limit:
        return text

    suffix = "\n... [truncated]"
    return text[: max(0, limit - len(suffix))] + suffix


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set")

    client.run(DISCORD_BOT_TOKEN)
