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
        "create_task, create_recurring_task, list_tasks, update_task, update_recurring_task, delete_task, delete_recurring_task, "
        "create_appointment, list_appointments, create_note, list_notes, create_expense, list_expenses, create_reminder, list_reminders, general_question. "
        "Para create_recurring_task, sempre exigir end_date e usar recurrence_pattern em: daily, weekly, monthly, interval. "
        "Para weekly, enviar recurrence_meta.weekdays como lista (ex.: [\"monday\",\"wednesday\"]). "
        "Para monthly, enviar recurrence_meta.day_of_month (1..31). "
        "Para interval, enviar recurrence_meta.every_days (>0). "
        "Para update_recurring_task e delete_recurring_task, enviar scope com single, future ou all. "
        "Se o usuário pedir editar/excluir algo recorrente e o scope não estiver explícito, defina precisa_confirmacao=true e pergunte exatamente: "
        "só esta tarefa? esta e as futuras? ou todas? "
        "Não invente dados faltantes. Se faltar dado essencial, use precisa_confirmacao=true. "
        "Use resposta_texto curta, clara e em português."
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
