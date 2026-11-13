from __future__ import annotations

from typing import Any


EDUCATION_LEVELS = ("Fundamental", "Médio/Técnico", "Superior")


def normalize_profile(profile: Any) -> dict[str, Any]:
    if not isinstance(profile, dict):
        profile = {}
    levels = profile.get("niveis_escolaridade", [])
    if not isinstance(levels, list):
        levels = []
    clean_levels = []
    for level in levels:
        if isinstance(level, str) and level in EDUCATION_LEVELS and level not in clean_levels:
            clean_levels.append(level)

    roles = profile.get("cargos_desejados", [])
    if isinstance(roles, str):
        roles = roles.splitlines()
    if not isinstance(roles, list):
        roles = []
    clean_roles = []
    for role in roles:
        if isinstance(role, str) and role.strip():
            clean = role.strip()
            if clean.casefold() not in {item.casefold() for item in clean_roles}:
                clean_roles.append(clean)

    notes = profile.get("observacoes", "")
    if not isinstance(notes, str):
        notes = ""
    return {
        "niveis_escolaridade": clean_levels,
        "cargos_desejados": clean_roles,
        "observacoes": notes.strip(),
    }


def profile_summary(profile: Any) -> str:
    clean = normalize_profile(profile)
    levels = ", ".join(clean["niveis_escolaridade"]) if clean["niveis_escolaridade"] else "Todos os níveis"
    roles = ", ".join(clean["cargos_desejados"]) if clean["cargos_desejados"] else "Todos os cargos dos níveis selecionados"
    return f"Níveis: {levels}. Cargos desejados: {roles}."
