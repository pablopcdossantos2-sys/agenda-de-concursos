from typing import Any


def format_cargo_salary(cargo: dict[str, Any]) -> str:
    initial = str(cargo.get("salario_inicial") or "").strip()
    final = str(cargo.get("salario_final") or "").strip()
    if initial and final and initial != final:
        return f"{initial} a {final}"
    if initial:
        return initial
    if final:
        return f"Até {final}"
    return "Não informada"
