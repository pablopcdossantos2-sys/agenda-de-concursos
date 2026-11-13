from __future__ import annotations

import json
from datetime import date
from typing import Any


SCHEMA_VERSION = 1
STATUSES = ("Sem Previsão", "Previsto", "Edital publicado")
TEXT_FIELDS = (
    "nome", "orgao", "cargo", "banca", "localidade", "url_edital",
    "url_oficial", "observacoes",
)
DATE_FIELDS = ("inscricoes_inicio", "inscricoes_fim", "data_prova")
CONTEST_KEYS = set(TEXT_FIELDS + DATE_FIELDS + ("data_prevista", "status", "prioridade", "disciplinas", "cargos"))
DISCIPLINE_KEYS = {"nome", "topicos"}
TOPIC_KEYS = {"nome", "nome_padronizado"}
CARGO_KEYS = {
    "nome", "nivel_escolaridade", "requisitos", "salario_inicial",
    "salario_final", "beneficios", "jornada", "vagas", "localidade",
    "observacoes",
}
CARGO_TEXT_FIELDS = tuple(CARGO_KEYS)


def _check_keys(value: dict[str, Any], allowed: set[str], context: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"Campo(s) não reconhecido(s) em {context}: {', '.join(unknown)}.")


def normalize_cargo(item: Any, context: str = "cargo") -> dict[str, str]:
    if not isinstance(item, dict):
        raise ValueError(f"{context} precisa ser um objeto JSON.")
    _check_keys(item, CARGO_KEYS, context)
    cleaned: dict[str, str] = {}
    for field in CARGO_TEXT_FIELDS:
        value = item.get(field, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            if field == "vagas" and isinstance(value, (int, float)) and not isinstance(value, bool):
                value = str(value)
            else:
                raise ValueError(f"O campo '{field}' em {context} precisa ser texto.")
        cleaned[field] = value.strip()
    if not cleaned["nome"]:
        raise ValueError(f"Informe o nome em {context}.")
    return cleaned


def normalize_contest_payload(payload: Any) -> dict[str, Any]:
    """Valida uma ficha JSON sem executar qualquer código fornecido por terceiros."""
    if not isinstance(payload, dict):
        raise ValueError("O conteúdo precisa ser um objeto JSON.")
    _check_keys(payload, {"schema_version", "concurso"}, "raiz")
    if type(payload.get("schema_version")) is not int or payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"Versão de código não suportada. Use schema_version: {SCHEMA_VERSION}.")

    contest = payload.get("concurso")
    if not isinstance(contest, dict):
        raise ValueError("O campo 'concurso' precisa ser um objeto JSON.")
    _check_keys(contest, CONTEST_KEYS, "concurso")

    cleaned: dict[str, Any] = {}
    for field in TEXT_FIELDS:
        value = contest.get(field, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValueError(f"O campo '{field}' precisa ser texto.")
        cleaned[field] = value.strip()

    if not cleaned["nome"]:
        raise ValueError("O campo 'nome' é obrigatório.")

    status = contest.get("status", "Sem Previsão") or "Sem Previsão"
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("O campo 'status' deve ser 'Sem Previsão', 'Previsto' ou 'Edital publicado'.")
    cleaned["status"] = status

    for field in DATE_FIELDS:
        value = contest.get(field, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValueError(f"O campo '{field}' precisa ser uma data no formato AAAA-MM-DD ou vazio.")
        value = value.strip()
        if value:
            try:
                parsed = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"Data inválida em '{field}': use AAAA-MM-DD.") from exc
            if parsed.isoformat() != value:
                raise ValueError(f"Data inválida em '{field}': use AAAA-MM-DD.")
        cleaned[field] = value

    priority = contest.get("prioridade", False)
    if isinstance(priority, bool):
        cleaned["prioridade"] = int(priority)
    elif type(priority) is int and priority in (0, 1):
        cleaned["prioridade"] = priority
    else:
        raise ValueError("O campo 'prioridade' deve ser true, false, 1 ou 0.")

    cargos = contest.get("cargos", [])
    if not isinstance(cargos, list):
        raise ValueError("O campo 'cargos' precisa ser uma lista.")
    cleaned["cargos"] = [
        normalize_cargo(item, f"cargos[{index}]")
        for index, item in enumerate(cargos)
    ]

    disciplines = contest.get("disciplinas", [])
    if not isinstance(disciplines, list):
        raise ValueError("O campo 'disciplinas' precisa ser uma lista.")
    normalized_disciplines = []
    for discipline_index, discipline in enumerate(disciplines, start=1):
        context = f"disciplinas[{discipline_index - 1}]"
        if not isinstance(discipline, dict):
            raise ValueError(f"{context} precisa ser um objeto.")
        _check_keys(discipline, DISCIPLINE_KEYS, context)
        name = discipline.get("nome", "")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Informe o nome da disciplina em {context}.")
        topics = discipline.get("topicos", [])
        if not isinstance(topics, list):
            raise ValueError(f"O campo 'topicos' de {context} precisa ser uma lista.")
        normalized_topics = []
        for topic_index, topic in enumerate(topics, start=1):
            topic_context = f"{context}.topicos[{topic_index - 1}]"
            if isinstance(topic, str):
                topic = {"nome": topic}
            if not isinstance(topic, dict):
                raise ValueError(f"{topic_context} precisa ser um objeto ou texto.")
            _check_keys(topic, TOPIC_KEYS, topic_context)
            topic_name = topic.get("nome", "")
            canonical = topic.get("nome_padronizado", "")
            if not isinstance(topic_name, str) or not topic_name.strip():
                raise ValueError(f"Informe o nome do tópico em {topic_context}.")
            if canonical is None:
                canonical = ""
            if not isinstance(canonical, str):
                raise ValueError(f"O nome padronizado em {topic_context} precisa ser texto.")
            normalized_topics.append({
                "nome": topic_name.strip(),
                "nome_padronizado": canonical.strip(),
            })
        normalized_disciplines.append({
            "nome": name.strip(),
            "topicos": normalized_topics,
        })

    cleaned["disciplinas"] = normalized_disciplines
    # data_prevista é aceito somente para compatibilidade com JSON antigos;
    # não é persistido nem utilizado pelo sistema atual.
    return {"schema_version": SCHEMA_VERSION, "concurso": cleaned}


def parse_contest_json(source: str) -> dict[str, Any]:
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Cole o código JSON da ficha do concurso.")
    try:
        payload = json.loads(source)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON inválido na linha {exc.lineno}, coluna {exc.colno}: {exc.msg}."
        ) from exc
    return normalize_contest_payload(payload)
