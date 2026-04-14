from __future__ import annotations

import json
from typing import Any

from openai import OpenAI


def _build_system_prompt() -> str:
    return (
        "Você é o orquestrador do assistente Jarvis. "
        "Você NÃO executa SQL e NÃO inventa consultas ao banco. "
        "O backend já consulta o SQLite, fornece contexto estruturado e executará ações com base no seu JSON. "
        "Use o contexto para responder perguntas sobre tarefas, compromissos, lembretes, gastos e notas. "
        "Nunca solicite acesso direto ao banco. "
        "Responda somente com JSON válido e sem markdown, exatamente neste formato: "
        '{"resposta_texto":"string","acao_detectada":"string ou null","entidade":"string ou null","dados_extraidos":{},"precisa_confirmacao":true/false}. '
        "Intenções permitidas em acao_detectada: "
        "create_task, list_tasks, create_appointment, list_appointments, create_note, list_notes, "
        "create_expense, list_expenses, create_reminder, list_reminders, general_question. "
        "Use resposta_texto curta, objetiva e em português para economizar tokens. "
        "Se faltar dado essencial para criação, defina precisa_confirmacao=true e explique o que falta."
    )


def build_chat_completion(
    *,
    api_key: str,
    model: str,
    user_message: str,
    context: dict[str, Any],
    now_iso: str,
) -> dict[str, Any]:
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": _build_system_prompt(),
            },
            {
                "role": "user",
                "content": (
                    f"Data/hora atual (UTC): {now_iso}\n"
                    f"Mensagem do usuário: {user_message}\n"
                    f"Contexto estruturado do banco: {json.dumps(context, ensure_ascii=False)}"
                ),
            },
        ],
    )
    payload = response.output_text.strip()
    return json.loads(payload)
