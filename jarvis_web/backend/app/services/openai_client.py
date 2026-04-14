from openai import OpenAI

from app.core.config import settings


def ask_openai(message: str) -> str:
    if not settings.openai_api_key:
        return (
            "OPENAI_API_KEY não configurada. Mensagem recebida com sucesso: "
            f"{message[:180]}"
        )

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "system",
                "content": (
                    "Você é Jarvis, assistente pessoal focado em organização, "
                    "tarefas e produtividade. Seja objetivo e útil."
                ),
            },
            {"role": "user", "content": message},
        ],
    )
    return response.output_text
