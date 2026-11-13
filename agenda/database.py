from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


CONTEST_FIELDS = (
    "nome", "orgao", "cargo", "banca", "localidade", "status",
    "inscricoes_inicio", "inscricoes_fim", "data_prova", "data_prevista",
    "url_edital", "url_oficial", "observacoes", "prioridade",
)


class Database:
    """Repositório SQLite local. Cada operação usa uma conexão curta e segura."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS concursos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    orgao TEXT NOT NULL DEFAULT '',
                    cargo TEXT NOT NULL DEFAULT '',
                    banca TEXT NOT NULL DEFAULT '',
                    localidade TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'Sem Previsão',
                    inscricoes_inicio TEXT,
                    inscricoes_fim TEXT,
                    data_prova TEXT,
                    data_prevista TEXT,
                    url_edital TEXT NOT NULL DEFAULT '',
                    url_oficial TEXT NOT NULL DEFAULT '',
                    observacoes TEXT NOT NULL DEFAULT '',
                    prioridade INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS disciplinas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concurso_id INTEGER NOT NULL REFERENCES concursos(id) ON DELETE CASCADE,
                    nome TEXT NOT NULL,
                    ordem INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS topicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    disciplina_id INTEGER NOT NULL REFERENCES disciplinas(id) ON DELETE CASCADE,
                    nome TEXT NOT NULL,
                    nome_padronizado TEXT NOT NULL DEFAULT '',
                    ordem INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_disciplinas_concurso ON disciplinas(concurso_id);
                CREATE INDEX IF NOT EXISTS idx_topicos_disciplina ON topicos(disciplina_id);
                """
            )

    @staticmethod
    def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def list_contests(self, search: str = "") -> list[dict[str, Any]]:
        with self._connect() as db:
            if search.strip():
                term = f"%{search.strip()}%"
                rows = db.execute(
                    """SELECT * FROM concursos
                       WHERE nome LIKE ? OR orgao LIKE ? OR cargo LIKE ? OR banca LIKE ?
                       ORDER BY COALESCE(data_prova, data_prevista, '9999-12-31'), nome""",
                    (term, term, term, term),
                ).fetchall()
            else:
                rows = db.execute(
                    """SELECT * FROM concursos
                       ORDER BY COALESCE(data_prova, data_prevista, '9999-12-31'), nome"""
                ).fetchall()
            return [dict(row) for row in rows]

    def get_contest(self, contest_id: int) -> dict[str, Any] | None:
        with self._connect() as db:
            return self._dict(db.execute(
                "SELECT * FROM concursos WHERE id = ?", (contest_id,)
            ).fetchone())

    def save_contest(self, data: dict[str, Any], contest_id: int | None = None) -> int:
        nome = str(data.get("nome", "")).strip()
        if not nome:
            raise ValueError("Informe o nome do concurso ou processo seletivo.")
        values = {field: data.get(field) for field in CONTEST_FIELDS}
        values["nome"] = nome
        values["status"] = values.get("status") or "Sem Previsão"
        for field in ("orgao", "cargo", "banca", "localidade", "url_edital", "url_oficial", "observacoes"):
            values[field] = values.get(field) or ""
        values["prioridade"] = int(values.get("prioridade") or 0)
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as db:
            if contest_id is None:
                columns = list(CONTEST_FIELDS) + ["created_at", "updated_at"]
                placeholders = ", ".join("?" for _ in columns)
                cursor = db.execute(
                    f"INSERT INTO concursos ({', '.join(columns)}) VALUES ({placeholders})",
                    [values.get(field) for field in CONTEST_FIELDS] + [now, now],
                )
                return int(cursor.lastrowid)
            assignments = ", ".join(f"{field} = ?" for field in CONTEST_FIELDS)
            db.execute(
                f"UPDATE concursos SET {assignments}, updated_at = ? WHERE id = ?",
                [values.get(field) for field in CONTEST_FIELDS] + [now, contest_id],
            )
            return contest_id

    def delete_contest(self, contest_id: int) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM concursos WHERE id = ?", (contest_id,))

    def count_contests(self) -> int:
        with self._connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM concursos").fetchone()[0])

    def add_discipline(self, contest_id: int, name: str) -> int:
        clean = name.strip()
        if not clean:
            raise ValueError("Informe o nome da disciplina.")
        with self._connect() as db:
            order = db.execute(
                "SELECT COALESCE(MAX(ordem), -1) + 1 FROM disciplinas WHERE concurso_id = ?",
                (contest_id,),
            ).fetchone()[0]
            cursor = db.execute(
                "INSERT INTO disciplinas (concurso_id, nome, ordem) VALUES (?, ?, ?)",
                (contest_id, clean, order),
            )
            return int(cursor.lastrowid)

    def list_disciplines(self, contest_id: int) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM disciplinas WHERE concurso_id = ? ORDER BY ordem, nome",
                (contest_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def rename_discipline(self, discipline_id: int, name: str) -> None:
        if not name.strip():
            raise ValueError("O nome da disciplina não pode ficar vazio.")
        with self._connect() as db:
            db.execute("UPDATE disciplinas SET nome = ? WHERE id = ?", (name.strip(), discipline_id))

    def delete_discipline(self, discipline_id: int) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM disciplinas WHERE id = ?", (discipline_id,))

    def add_topic(self, discipline_id: int, name: str, canonical_name: str = "") -> int:
        clean = name.strip()
        if not clean:
            raise ValueError("Informe o tópico.")
        with self._connect() as db:
            order = db.execute(
                "SELECT COALESCE(MAX(ordem), -1) + 1 FROM topicos WHERE disciplina_id = ?",
                (discipline_id,),
            ).fetchone()[0]
            cursor = db.execute(
                """INSERT INTO topicos (disciplina_id, nome, nome_padronizado, ordem)
                   VALUES (?, ?, ?, ?)""",
                (discipline_id, clean, canonical_name.strip(), order),
            )
            return int(cursor.lastrowid)

    def update_topic(self, topic_id: int, name: str, canonical_name: str = "") -> None:
        if not name.strip():
            raise ValueError("O tópico não pode ficar vazio.")
        with self._connect() as db:
            db.execute(
                "UPDATE topicos SET nome = ?, nome_padronizado = ? WHERE id = ?",
                (name.strip(), canonical_name.strip(), topic_id),
            )

    def list_topics(self, discipline_id: int) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM topicos WHERE disciplina_id = ? ORDER BY ordem, nome",
                (discipline_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_topic(self, topic_id: int) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM topicos WHERE id = ?", (topic_id,))

    def get_program(self, contest_id: int) -> list[dict[str, Any]]:
        disciplines = self.list_disciplines(contest_id)
        for discipline in disciplines:
            discipline["topicos"] = self.list_topics(discipline["id"])
        return disciplines

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as db:
            row = db.execute(
                "SELECT valor FROM configuracoes WHERE chave = ?", (key,)
            ).fetchone()
            return str(row["valor"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO configuracoes (chave, valor) VALUES (?, ?)
                   ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
                (key, str(value)),
            )

    def export_json(self, destination: Path | str) -> None:
        with self._connect() as db:
            contests = [dict(r) for r in db.execute("SELECT * FROM concursos ORDER BY id")]
            disciplines = [dict(r) for r in db.execute("SELECT * FROM disciplinas ORDER BY id")]
            topics = [dict(r) for r in db.execute("SELECT * FROM topicos ORDER BY id")]
            settings = {r["chave"]: r["valor"] for r in db.execute("SELECT * FROM configuracoes")}
        payload = {
            "schema_version": 1,
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "concursos": contests,
            "disciplinas": disciplines,
            "topicos": topics,
            "configuracoes": settings,
        }
        Path(destination).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def import_json(self, source: Path | str) -> None:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ValueError("Versão de backup não reconhecida.")
        contests = payload.get("concursos", [])
        disciplines = payload.get("disciplinas", [])
        topics = payload.get("topicos", [])
        settings = payload.get("configuracoes", {})
        if not all(isinstance(x, list) for x in (contests, disciplines, topics)):
            raise ValueError("Estrutura do backup inválida.")
        with self._connect() as db:
            db.execute("DELETE FROM topicos")
            db.execute("DELETE FROM disciplinas")
            db.execute("DELETE FROM concursos")
            for row in contests:
                fields = [f for f in CONTEST_FIELDS if f in row]
                fields = ["id"] + fields + ["created_at", "updated_at"]
                values = [row["id"]] + [row.get(f) for f in fields[1:-2]] + [
                    row.get("created_at", datetime.now().isoformat(timespec="seconds")),
                    row.get("updated_at", datetime.now().isoformat(timespec="seconds")),
                ]
                db.execute(
                    f"INSERT INTO concursos ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
                    values,
                )
            for row in disciplines:
                db.execute(
                    "INSERT INTO disciplinas (id, concurso_id, nome, ordem) VALUES (?, ?, ?, ?)",
                    (row["id"], row["concurso_id"], row["nome"], row.get("ordem", 0)),
                )
            for row in topics:
                db.execute(
                    """INSERT INTO topicos (id, disciplina_id, nome, nome_padronizado, ordem)
                       VALUES (?, ?, ?, ?, ?)""",
                    (row["id"], row["disciplina_id"], row["nome"],
                     row.get("nome_padronizado", ""), row.get("ordem", 0)),
                )
            db.execute("DELETE FROM configuracoes")
            for key, value in settings.items():
                db.execute("INSERT INTO configuracoes (chave, valor) VALUES (?, ?)", (key, str(value)))
