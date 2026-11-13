from __future__ import annotations

import re
from datetime import date


MONTHS = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)


def parse_user_date(value: str) -> str:
    """Converte AAAA-MM-DD, DD/MM/AAAA ou DD-MM-AAAA para ISO."""
    clean = (value or "").strip()
    if not clean:
        return ""
    patterns = (
        (r"^(\d{4})-(\d{2})-(\d{2})$", "%Y-%m-%d"),
        (r"^(\d{2})/(\d{2})/(\d{4})$", "%d/%m/%Y"),
        (r"^(\d{2})-(\d{2})-(\d{4})$", "%d-%m-%Y"),
    )
    from datetime import datetime
    for pattern, fmt in patterns:
        if re.match(pattern, clean):
            try:
                return datetime.strptime(clean, fmt).date().isoformat()
            except ValueError as exc:
                raise ValueError("Data inválida. Use DD/MM/AAAA.") from exc
    raise ValueError("Data inválida. Use DD/MM/AAAA.")


def format_date_pt_br(value: str | None) -> str:
    """Apresenta uma data ISO como '12 de Novembro de 2026'."""
    clean = str(value or "").strip()
    if not clean:
        return "Não informado"
    try:
        parsed = date.fromisoformat(clean)
    except ValueError:
        try:
            parsed = date.fromisoformat(parse_user_date(clean))
        except ValueError:
            return clean
    return f"{parsed.day} de {MONTHS[parsed.month - 1]} de {parsed.year}"


def format_datetime_pt_br(value: str | None) -> str:
    clean = str(value or "").strip()
    if not clean:
        return "Não informado"
    try:
        from datetime import datetime
        parsed = datetime.fromisoformat(clean)
        return f"{parsed.day} de {MONTHS[parsed.month - 1]} de {parsed.year}, {parsed:%H:%M}"
    except ValueError:
        return clean
