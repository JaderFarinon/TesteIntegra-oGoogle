from __future__ import annotations

import json
from typing import Any

from openai import OpenAI


def build_chat_completion(
    *,
    api_key: str,
    model: str,
    user_message: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "Você é um assistente pessoal de produtividade. "
                    "Responda SOMENTE com JSON válido no formato: "
                    "{resposta_texto, acao_detectada, entidade, dados_extraidos, precisa_confirmacao}. "
                    "A acao_detectada deve ser uma de: create, update, delete, none."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Mensagem do usuário: {user_message}\n"
                    f"Contexto do banco: {json.dumps(context, ensure_ascii=False)}"
                ),
            },
        ],
    )
    payload = response.output_text.strip()
    return json.loads(payload)
