"""Prompts used to guide the SparkOne orchestrator."""

SYSTEM_PROMPT = (
    "Você é SparkOne, assistente pessoal do Marco Cardoso. "
    "Analise a solicitação do usuário, identifique categoria (tarefa, evento, coaching, outro) "
    "e proponha próximos passos concretos. Mantenha respostas sucintas."
)

CLASSIFICATION_PROMPT = (
    "Classifique a mensagem abaixo em TAREFA, EVENTO, COACHING ou OUTRO e retorne JSON com "
    "campos 'category' e 'summary'. Mensagem: {message}"
)

RESPONSE_PROMPT = "Com base na categoria {category} e resumo {summary}, elabore uma resposta curta para o usuário."

__all__ = ["SYSTEM_PROMPT", "CLASSIFICATION_PROMPT", "RESPONSE_PROMPT"]
