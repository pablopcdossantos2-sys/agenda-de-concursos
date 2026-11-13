from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


STOP_WORDS = {
    "a", "as", "o", "os", "de", "da", "das", "do", "dos", "e", "ou",
    "em", "no", "na", "nos", "nas", "para", "por", "com", "um", "uma",
    "que", "se", "ao", "aos", "à", "às", "sob", "sobre",
}


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _tokens(value: str) -> set[str]:
    return {token for token in normalize(value).split() if token not in STOP_WORDS and len(token) > 1}


def lexical_similarity(left: str, right: str) -> float:
    a, b = normalize(left), normalize(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ta, tb = _tokens(a), _tokens(b)
    union = ta | tb
    jaccard = len(ta & tb) / len(union) if union else 0.0
    sequence = SequenceMatcher(None, a, b).ratio()
    return min(1.0, 0.65 * jaccard + 0.35 * sequence)


def topic_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    canonical_left = normalize(left.get("nome_padronizado", ""))
    canonical_right = normalize(right.get("nome_padronizado", ""))
    if canonical_left and canonical_right and canonical_left == canonical_right:
        return 1.0
    return lexical_similarity(left.get("nome", ""), right.get("nome", ""))


def _match_topics(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> dict[str, Any]:
    candidates: list[tuple[float, int, int]] = []
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            score = topic_similarity(a, b)
            if score >= 0.34:
                candidates.append((score, i, j))
    candidates.sort(reverse=True)
    used_left: set[int] = set()
    used_right: set[int] = set()
    matches: list[dict[str, Any]] = []
    for score, i, j in candidates:
        if i in used_left or j in used_right:
            continue
        used_left.add(i)
        used_right.add(j)
        matches.append({
            "topico_a": left[i].get("nome", ""),
            "topico_b": right[j].get("nome", ""),
            "similaridade": round(score * 100, 1),
            "padronizado": bool(
                normalize(left[i].get("nome_padronizado", ""))
                and normalize(left[i].get("nome_padronizado", ""))
                == normalize(right[j].get("nome_padronizado", ""))
            ),
        })
    unmatched_left = [item.get("nome", "") for i, item in enumerate(left) if i not in used_left]
    unmatched_right = [item.get("nome", "") for j, item in enumerate(right) if j not in used_right]
    denominator = max(len(left), len(right), 1)
    score = sum(item["similaridade"] / 100 for item in matches) / denominator
    return {
        "similaridade": score,
        "matches": matches,
        "somente_a": unmatched_left,
        "somente_b": unmatched_right,
        "total_a": len(left),
        "total_b": len(right),
    }


def compare_programs(program_a: list[dict[str, Any]], program_b: list[dict[str, Any]]) -> dict[str, Any]:
    """Compara disciplinas e tópicos; retorna uma métrica e sua decomposição."""
    left = list(program_a)
    right = list(program_b)
    candidates: list[tuple[float, int, int]] = []
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            score = lexical_similarity(a.get("nome", ""), b.get("nome", ""))
            if score >= 0.55:
                candidates.append((score, i, j))
    candidates.sort(reverse=True)

    used_left: set[int] = set()
    used_right: set[int] = set()
    pairs: list[tuple[int, int, float]] = []
    for score, i, j in candidates:
        if i not in used_left and j not in used_right:
            used_left.add(i)
            used_right.add(j)
            pairs.append((i, j, score))

    results: list[dict[str, Any]] = []
    weighted_score = 0.0
    total_weight = 0
    for i, j, name_score in pairs:
        a, b = left[i], right[j]
        detail = _match_topics(a.get("topicos", []), b.get("topicos", []))
        weight = max(detail["total_a"], detail["total_b"], 1)
        combined = detail["similaridade"] * 0.90 + name_score * 0.10
        weighted_score += combined * weight
        total_weight += weight
        results.append({
            "disciplina_a": a.get("nome", ""),
            "disciplina_b": b.get("nome", ""),
            "similaridade": round(combined * 100, 1),
            "topicos": detail,
        })

    for i, discipline in enumerate(left):
        if i in used_left:
            continue
        weight = max(len(discipline.get("topicos", [])), 1)
        total_weight += weight
        results.append({
            "disciplina_a": discipline.get("nome", ""),
            "disciplina_b": None,
            "similaridade": 0.0,
            "topicos": {
                "similaridade": 0.0, "matches": [],
                "somente_a": [t.get("nome", "") for t in discipline.get("topicos", [])],
                "somente_b": [], "total_a": len(discipline.get("topicos", [])), "total_b": 0,
            },
        })

    for j, discipline in enumerate(right):
        if j in used_right:
            continue
        weight = max(len(discipline.get("topicos", [])), 1)
        total_weight += weight
        results.append({
            "disciplina_a": None,
            "disciplina_b": discipline.get("nome", ""),
            "similaridade": 0.0,
            "topicos": {
                "similaridade": 0.0, "matches": [],
                "somente_a": [], "somente_b": [t.get("nome", "") for t in discipline.get("topicos", [])],
                "total_a": 0, "total_b": len(discipline.get("topicos", [])),
            },
        })

    percentage = (weighted_score / total_weight * 100) if total_weight else 0.0
    matching_topics = sum(len(row["topicos"]["matches"]) for row in results)
    only_a = sum(len(row["topicos"]["somente_a"]) for row in results)
    only_b = sum(len(row["topicos"]["somente_b"]) for row in results)
    return {
        "percentual": round(percentage, 1),
        "disciplinas_comparadas": len(pairs),
        "topicos_correspondentes": matching_topics,
        "topicos_exclusivos_a": only_a,
        "topicos_exclusivos_b": only_b,
        "disciplinas": sorted(results, key=lambda row: (
            normalize(row.get("disciplina_a") or row.get("disciplina_b") or "")
        )),
        "metodologia": (
            "Correspondência por disciplina e similaridade textual dos tópicos. "
            "Nomes padronizados iguais são tratados como correspondência explícita. "
            "A pontuação pondera tópicos correspondentes pela quantidade de tópicos "
            "da maior lista de cada disciplina."
        ),
    }
