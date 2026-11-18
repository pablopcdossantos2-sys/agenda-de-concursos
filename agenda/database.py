from __future__ import annotations

import json
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterator

from agenda.services.contest_payload import normalize_contest_payload
from agenda.services.profile import normalize_profile


CONTEST_FIELDS = (
    "nome", "orgao", "cargo", "banca", "localidade", "status",
    "inscricoes_inicio", "inscricoes_fim", "data_prova",
    "url_edital", "url_oficial", "observacoes", "prioridade",
)
CARGO_FIELDS = (
    "nome", "nivel_escolaridade", "requisitos", "salario_inicial",
    "salario_final", "beneficios", "jornada", "vagas", "localidade", "observacoes",
)


def _search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


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

                CREATE TABLE IF NOT EXISTS cargos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concurso_id INTEGER NOT NULL REFERENCES concursos(id) ON DELETE CASCADE,
                    nome TEXT NOT NULL,
                    nivel_escolaridade TEXT NOT NULL DEFAULT '',
                    requisitos TEXT NOT NULL DEFAULT '',
                    salario_inicial TEXT NOT NULL DEFAULT '',
                    salario_final TEXT NOT NULL DEFAULT '',
                    beneficios TEXT NOT NULL DEFAULT '',
                    jornada TEXT NOT NULL DEFAULT '',
                    vagas TEXT NOT NULL DEFAULT '',
                    localidade TEXT NOT NULL DEFAULT '',
                    observacoes TEXT NOT NULL DEFAULT '',
                    interesse INTEGER NOT NULL DEFAULT 0 CHECK (interesse IN (0, 1)),
                    ordem INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_disciplinas_concurso ON disciplinas(concurso_id);
                CREATE INDEX IF NOT EXISTS idx_cargos_concurso ON cargos(concurso_id);
                CREATE INDEX IF NOT EXISTS idx_topicos_disciplina ON topicos(disciplina_id);
                """
            )
            db.execute("BEGIN IMMEDIATE")
            if "interesse" not in {row["name"] for row in db.execute("PRAGMA table_info(cargos)")}:
                db.execute(
                    "ALTER TABLE cargos ADD COLUMN interesse INTEGER NOT NULL DEFAULT 0 "
                    "CHECK (interesse IN (0, 1))"
                )

    @staticmethod
    def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def list_contests(self, search: str = "") -> list[dict[str, Any]]:
        with self._connect() as db:
            if search.strip():
                db.create_function("search_text", 1, _search_text, deterministic=True)
                term = _search_text(search.strip())
                rows = db.execute(
                    """SELECT * FROM concursos
                       WHERE instr(search_text(nome), :term) > 0
                          OR instr(search_text(orgao), :term) > 0
                          OR instr(search_text(cargo), :term) > 0
                          OR instr(search_text(banca), :term) > 0
                          OR EXISTS (
                              SELECT 1 FROM cargos
                              WHERE cargos.concurso_id = concursos.id
                                AND instr(search_text(cargos.nome), :term) > 0
                          )
                       ORDER BY COALESCE(NULLIF(data_prova, ''), '9999-12-31'), nome""",
                    {"term": term},
                ).fetchall()
            else:
                rows = db.execute(
                    """SELECT * FROM concursos
                       ORDER BY COALESCE(NULLIF(data_prova, ''), '9999-12-31'), nome"""
                ).fetchall()
            return [dict(row) for row in rows]

    def get_contest(self, contest_id: int) -> dict[str, Any] | None:
        with self._connect() as db:
            return self._dict(db.execute(
                "SELECT * FROM concursos WHERE id = ?", (contest_id,)
            ).fetchone())

    def save_contest(self, data: dict[str, Any], contest_id: int | None = None) -> int:
        with self._connect() as db:
            saved_id = self._save_contest(db, data, contest_id)
            if "cargos" in data:
                self._replace_cargos(db, saved_id, data["cargos"])
            return saved_id

    @staticmethod
    def _save_contest(
        db: sqlite3.Connection, data: dict[str, Any], contest_id: int | None = None
    ) -> int:
        values = {field: data.get(field) or "" for field in CONTEST_FIELDS}
        values["nome"] = str(values["nome"]).strip()
        if not values["nome"]:
            raise ValueError("Informe o nome do concurso ou processo seletivo.")
        values["status"] = values["status"] or "Sem Previsão"
        values["prioridade"] = int(values["prioridade"] or 0)
        for field in ("inscricoes_inicio", "inscricoes_fim", "data_prova"):
            values[field] = values[field] or None
        now = datetime.now().isoformat(timespec="seconds")
        params = [values[field] for field in CONTEST_FIELDS]
        if contest_id is None:
            columns = (*CONTEST_FIELDS, "created_at", "updated_at")
            placeholders = ", ".join("?" for _ in columns)
            cursor = db.execute(
                f"INSERT INTO concursos ({', '.join(columns)}) VALUES ({placeholders})",
                [*params, now, now],
            )
            return int(cursor.lastrowid)
        assignments = ", ".join(f"{field} = ?" for field in CONTEST_FIELDS)
        cursor = db.execute(
            f"UPDATE concursos SET {assignments}, updated_at = ? WHERE id = ?",
            [*params, now, contest_id],
        )
        if not cursor.rowcount:
            raise ValueError("O concurso selecionado não existe.")
        return contest_id

    def add_contest_payload(self, payload: dict[str, Any]) -> int:
        """Cria concurso, disciplinas e tópicos numa única transação SQLite."""
        normalized = normalize_contest_payload(payload)
        contest = normalized["concurso"]
        with self._connect() as db:
            contest_id = self._save_contest(db, contest)
            for discipline_order, discipline in enumerate(contest["disciplinas"]):
                discipline_cursor = db.execute(
                    "INSERT INTO disciplinas (concurso_id, nome, ordem) VALUES (?, ?, ?)",
                    (contest_id, discipline["nome"], discipline_order),
                )
                discipline_id = int(discipline_cursor.lastrowid)
                for topic_order, topic in enumerate(discipline["topicos"]):
                    db.execute(
                        """INSERT INTO topicos (disciplina_id, nome, nome_padronizado, ordem)
                           VALUES (?, ?, ?, ?)""",
                        (
                            discipline_id,
                            topic["nome"],
                            topic.get("nome_padronizado", ""),
                            topic_order,
                        ),
                    )
            for order, cargo in enumerate(contest["cargos"]):
                self._insert_cargo(db, contest_id, cargo, order)
        return contest_id

    @staticmethod
    def _insert_cargo(db: sqlite3.Connection, contest_id: int, cargo: dict[str, Any], order: int) -> int:
        values = [str(cargo.get(field) or "").strip() for field in CARGO_FIELDS]
        cursor = db.execute(
            f"INSERT INTO cargos (concurso_id, {', '.join(CARGO_FIELDS)}, interesse, ordem) "
            f"VALUES ({', '.join('?' for _ in range(len(CARGO_FIELDS) + 3))})",
            [contest_id, *values, int(cargo.get("interesse") in (True, 1)), order],
        )
        return int(cursor.lastrowid)

    def list_cargos(self, contest_id: int) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM cargos WHERE concurso_id = ? ORDER BY ordem, nome",
                (contest_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def replace_cargos(self, contest_id: int, cargos: list[dict[str, Any]]) -> None:
        with self._connect() as db:
            exists = db.execute("SELECT 1 FROM concursos WHERE id = ?", (contest_id,)).fetchone()
            if not exists:
                raise ValueError("O concurso selecionado não existe.")
            self._replace_cargos(db, contest_id, cargos)

    def _replace_cargos(
        self, db: sqlite3.Connection, contest_id: int, cargos: list[dict[str, Any]]
    ) -> None:
        if not isinstance(cargos, list):
            raise ValueError("A lista de cargos é inválida.")
        for index, cargo in enumerate(cargos):
            if not isinstance(cargo, dict) or not str(cargo.get("nome") or "").strip():
                raise ValueError(f"Informe o nome do cargo na posição {index + 1}.")
        db.execute("DELETE FROM cargos WHERE concurso_id = ?", (contest_id,))
        for order, cargo in enumerate(cargos):
            self._insert_cargo(db, contest_id, cargo, order)

    def save_cargo(self, contest_id: int, cargo: dict[str, Any], cargo_id: int | None = None) -> int:
        if not str(cargo.get("nome") or "").strip():
            raise ValueError("Informe o nome do cargo.")
        with self._connect() as db:
            if cargo_id is None:
                order = db.execute(
                    "SELECT COALESCE(MAX(ordem), -1) + 1 FROM cargos WHERE concurso_id = ?",
                    (contest_id,),
                ).fetchone()[0]
                return self._insert_cargo(db, contest_id, cargo, order)
            values = [str(cargo.get(field) or "").strip() for field in CARGO_FIELDS]
            assignments = ", ".join(f"{field} = ?" for field in CARGO_FIELDS)
            interest = int(cargo["interesse"] in (True, 1)) if "interesse" in cargo else None
            db.execute(
                f"UPDATE cargos SET {assignments}, interesse = COALESCE(?, interesse) "
                "WHERE id = ? AND concurso_id = ?",
                [*values, interest, cargo_id, contest_id],
            )
            return cargo_id

    def delete_cargo(self, contest_id: int, cargo_id: int) -> None:
        with self._connect() as db:
            db.execute(
                "DELETE FROM cargos WHERE id = ? AND concurso_id = ?",
                (cargo_id, contest_id),
            )

    def get_user_profile(self) -> dict[str, Any]:
        raw = self.get_setting("user_profile", "{}")
        try:
            return normalize_profile(json.loads(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            return normalize_profile({})

    def save_user_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_profile(profile)
        self.set_setting("user_profile", json.dumps(normalized, ensure_ascii=False))
        return normalized

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
        target = Path(destination)
        for source in (self.path, Path(f"{self.path}-wal"), Path(f"{self.path}-shm")):
            if target.resolve() == source.resolve() or (
                target.exists() and source.exists() and target.samefile(source)
            ):
                raise ValueError("Escolha um arquivo de backup diferente dos arquivos do banco de dados.")
        with self._connect() as db:
            db.execute("BEGIN")
            backup_fields = ["id"] + list(CONTEST_FIELDS) + ["created_at", "updated_at"]
            contests = [
                {field: row[field] for field in backup_fields}
                for row in db.execute(
                    f"SELECT {', '.join(backup_fields)} FROM concursos ORDER BY id"
                )
            ]
            disciplines = [dict(r) for r in db.execute("SELECT * FROM disciplinas ORDER BY id")]
            topics = [dict(r) for r in db.execute("SELECT * FROM topicos ORDER BY id")]
            cargos = [dict(r) for r in db.execute("SELECT * FROM cargos ORDER BY id")]
            settings = {r["chave"]: r["valor"] for r in db.execute("SELECT * FROM configuracoes")}
        payload = {
            "schema_version": 1,
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "concursos": contests,
            "disciplinas": disciplines,
            "topicos": topics,
            "cargos": cargos,
            "configuracoes": settings,
        }
        output = NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent, suffix=".tmp", delete=False
        )
        temporary = Path(output.name)
        try:
            with output:
                json.dump(payload, output, ensure_ascii=False, indent=2)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)

    def import_json(self, source: Path | str) -> None:
        payload = json.loads(Path(source).read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("O backup precisa ser um objeto JSON.")
        if type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
            raise ValueError("Versão de backup não reconhecida.")
        contests = payload.get("concursos")
        disciplines = payload.get("disciplinas")
        topics = payload.get("topicos")
        cargos = payload.get("cargos", [])
        settings = payload.get("configuracoes", {})
        for key, rows, parent_id in (
            ("concursos", contests, None),
            ("disciplinas", disciplines, "concurso_id"),
            ("topicos", topics, "disciplina_id"),
            ("cargos", cargos, "concurso_id"),
        ):
            if not isinstance(rows, list):
                raise ValueError(f"A seção '{key}' do backup precisa ser uma lista.")
            for row in rows:
                if (
                    not isinstance(row, dict)
                    or not isinstance(row.get("nome"), str)
                    or not row["nome"].strip()
                    or type(row.get("id")) is not int
                    or (parent_id and type(row.get(parent_id)) is not int)
                ):
                    raise ValueError(f"Registro inválido na seção '{key}' do backup.")
        if not isinstance(settings, dict):
            raise ValueError("A seção 'configuracoes' do backup precisa ser um objeto.")
        with self._connect() as db:
            db.execute("DELETE FROM topicos")
            db.execute("DELETE FROM cargos")
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
            for row in cargos:
                values = [row.get(field, "") for field in CARGO_FIELDS]
                db.execute(
                    f"INSERT INTO cargos (id, concurso_id, {', '.join(CARGO_FIELDS)}, interesse, ordem) "
                    f"VALUES ({', '.join('?' for _ in range(len(CARGO_FIELDS) + 4))})",
                    [row["id"], row["concurso_id"], *values,
                     int(row.get("interesse") in (True, 1)), row.get("ordem", 0)],
                )
            db.execute("DELETE FROM configuracoes")
            for key, value in settings.items():
                db.execute("INSERT INTO configuracoes (chave, valor) VALUES (?, ?)", (key, str(value)))
