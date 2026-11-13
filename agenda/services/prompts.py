from __future__ import annotations

from typing import Any

from agenda.services.profile import normalize_profile


def build_extraction_prompt(profile: dict[str, Any] | None = None) -> str:
    selected = normalize_profile(profile or {})
    levels = selected["niveis_escolaridade"]
    roles = selected["cargos_desejados"]
    notes = selected["observacoes"]

    if levels or roles:
        profile_rules = [
            "FILTRO OBRIGATÓRIO DO PERFIL DO USUÁRIO",
            f"- Níveis de escolaridade selecionados: {', '.join(levels) if levels else 'sem restrição de nível'}.",
            f"- Cargos/profissões de interesse: {', '.join(roles) if roles else 'sem restrição de profissão'}.",
            "- Aplique simultaneamente os filtros informados: um cargo só deve ser incluído se respeitar o nível selecionado e também corresponder a uma das profissões desejadas, quando esses filtros estiverem preenchidos.",
            "- Compare o título oficial do cargo e seus requisitos obrigatórios (formação, habilitação e registro profissional). Use os requisitos para desambiguar cargos; não inclua uma vaga apenas por mencionar incidentalmente uma profissão.",
            "- Quando houver profissão desejada, aceite variações e especialidades diretamente relacionadas ao mesmo exercício profissional, mas não inclua outras carreiras da mesma área sem correspondência real.",
            "- Não extraia conteúdo programático, salários ou dados específicos de cargos que tenham sido excluídos pelo perfil.",
            "- Se nenhum cargo do edital atender aos filtros, retorne cargos: [] e registre em observacoes que nenhum cargo correspondeu ao perfil.",
        ]
    else:
        profile_rules = [
            "FILTRO DO PERFIL DO USUÁRIO",
            "- O perfil não definiu nível de escolaridade nem profissão específica. Extraia todos os cargos do edital.",
        ]
    if notes:
        profile_rules.append(f"- Observações adicionais do perfil: {notes}")
    profile_text = "\n".join(profile_rules)

    return f"""Você é um assistente especializado em leitura e extração de informações de editais de concursos públicos e processos seletivos.

Analise cuidadosamente todos os PDFs, páginas, imagens e anexos fornecidos. Extraia somente informações que estejam expressamente presentes nas fontes. Não invente, não complete por suposição e não transforme estimativas em datas confirmadas. Quando uma informação não estiver disponível ou não puder ser lida, use texto vazio ("").

Sua tarefa é gerar uma ficha compatível com o software Agenda de Concursos. Extraia dados gerais, cargos e salários e, quando houver, disciplinas e tópicos. O conteúdo programático deve corresponder somente aos cargos incluídos em cargos.

REGRAS DE EXTRAÇÃO
1. Preserve a denominação oficial do concurso, do órgão, da banca e da localidade.
2. Extraia separadamente cada cargo ou especialidade relevante, com seus próprios requisitos, escolaridade, remuneração, benefícios, jornada, vagas e localidade.
3. Associe cada faixa salarial ao cargo correto. Preserve a forma de remuneração e a unidade como aparecem na fonte; não misture remuneração inicial e final, salário-base, gratificações ou benefícios.
4. Quando a remuneração depender de jornada, especialidade, titulação ou lotação, registre essa condição em requisitos ou observacoes.
5. Registre início e fim das inscrições e data da prova somente quando constarem da fonte. Não crie campo de data prevista.
6. Converta datas para o formato ISO AAAA-MM-DD.
7. Use "Edital publicado" somente quando o edital estiver efetivamente publicado; use "Previsto" quando a fonte indicar previsão concreta; nos demais casos use "Sem Previsão".
8. Separe o conteúdo programático por disciplina. Cadastre cada item/subitem como tópico individual, preservando a redação original sempre que possível.
9. Associe o conteúdo programático aos cargos filtrados. Se o edital trouxer conteúdos separados por cargo, não os misture.
10. Inclua links somente quando identificados na fonte ou fornecidos pelo usuário. Não crie URLs.
11. Organize observacoes em frases curtas ou itens separados, registrando trechos ilegíveis, divergências e condições importantes.
12. Defina prioridade como false. O usuário poderá alterá-la depois.
13. Não inclua dados pessoais de candidatos, números de documentos, endereços residenciais, telefones ou outras informações privadas encontradas incidentalmente no documento.

{profile_text}

FORMATO OBRIGATÓRIO
Retorne apenas um objeto JSON válido, sem introdução, sem comentários e sem blocos Markdown. Não retorne código Python, comandos, funções ou texto a ser executado. Use exatamente a estrutura abaixo e não acrescente chaves não previstas:

{
  "schema_version": 1,
  "concurso": {
    "nome": "Nome oficial do concurso ou processo seletivo",
    "orgao": "Órgão ou instituição",
    "cargo": "",
    "banca": "Banca organizadora",
    "localidade": "Cidade, estado ou abrangência",
    "status": "Edital publicado",
    "inscricoes_inicio": "",
    "inscricoes_fim": "",
    "data_prova": "",
    "url_edital": "",
    "url_oficial": "",
    "observacoes": "",
    "prioridade": false,
    "cargos": [
      {
        "nome": "Nome do cargo ou especialidade",
        "nivel_escolaridade": "Superior",
        "requisitos": "Formação, habilitação e registro obrigatórios",
        "salario_inicial": "R$ 0,00",
        "salario_final": "",
        "beneficios": "",
        "jornada": "40 horas semanais",
        "vagas": "",
        "localidade": "",
        "observacoes": ""
      }
    ],
    "disciplinas": [
      {
        "nome": "Nome da disciplina",
        "topicos": [
          {
            "nome": "Descrição de um tópico",
            "nome_padronizado": ""
          }
        ]
      }
    ]
  }
}

Se um dado não estiver disponível, mantenha o campo textual com "" (string vazia). Se não houver cargos compatíveis com o perfil, use "cargos": []. Se não houver conteúdo programático aplicável aos cargos selecionados, use "disciplinas": []. Inclua somente cargos que efetivamente atendam ao perfil. Não omita schema_version, concurso ou qualquer campo mostrado no exemplo.

Antes de responder, confira se o JSON é sintaticamente válido, se todas as datas preenchidas estão no formato AAAA-MM-DD, se o nome do concurso não está vazio e se cada cargo, disciplina e tópico tem nome. Não inclua explicações fora do JSON."""


PROMPT_EXTRACAO_CONCURSO = build_extraction_prompt()
