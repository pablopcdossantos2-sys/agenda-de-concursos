# Perfil, extração de editais, cargos e importação JSON

## 1. Defina seu Perfil

1. Abra a seção **Perfil** no menu lateral.
2. Marque os níveis de escolaridade que aceita: Fundamental, Médio/Técnico e/ou Superior.
3. Se não marcar nenhum nível, o sistema entende que você aceita todos.
4. Informe um cargo ou profissão por linha, por exemplo:
   - Médico
   - Jornalista
   - Médico cardiologista
5. Acrescente requisitos adicionais, quando necessário, como registro profissional ativo, formação específica ou restrições a contratos temporários.
6. Clique em **Salvar perfil**.

Quando níveis e profissões forem informados, o prompt aplicará os filtros simultaneamente. Um cargo será incluído somente quando atender ao nível escolhido e corresponder a uma das profissões de interesse. Os requisitos obrigatórios (formação, habilitação e registro profissional) ajudam a distinguir vagas com nomes semelhantes.

## 2. Use a seção Prompts

1. Abra **Prompts** pela barra de ferramentas ou pelo menu lateral.
2. Confira o resumo do perfil mostrado no início da janela.
3. Copie o prompt apresentado.
4. Em uma ferramenta de IA que aceite arquivos, anexe o edital em PDF ou as imagens com as informações do concurso.
5. Cole o prompt e peça à IA para retornar somente o JSON no formato solicitado.
6. Confira se a IA extraiu apenas cargos compatíveis com o perfil. Se nenhum cargo atender aos filtros, o resultado esperado é uma lista de cargos vazia.

O prompt solicita que a IA associe cada faixa salarial ao cargo correto e mantenha separados remuneração inicial, remuneração final, benefícios, jornada, vagas, lotação e requisitos.

## 3. Cadastre ou importe a ficha

O aplicativo aceita o formulário convencional, incluindo o gerenciamento manual de cargos e salários, ou uma ficha completa gerada por IA:

1. Abra **Concursos** e escolha **Inserir por código JSON**.
2. Cole o objeto JSON no editor.
3. Clique em **Validar e adicionar**.
4. Se houver erro, corrija o JSON e tente novamente.
5. A ficha, os cargos, as disciplinas e os tópicos são gravados no SQLite.

A importação aceita exclusivamente JSON validado. O aplicativo **não executa Python, comandos ou scripts** recebidos de terceiros.

## 4. Estrutura aceita

O objeto deve conter schema_version igual a 1 e um objeto concurso. O nome do concurso é obrigatório. As datas são enviadas no formato ISO AAAA-MM-DD; na interface, os campos editáveis aceitam DD/MM/AAAA e as datas aparecem por extenso, como 12 de Novembro de 2026.

~~~json
{
  "schema_version": 1,
  "concurso": {
    "nome": "Concurso de exemplo",
    "orgao": "Órgão público",
    "cargo": "",
    "banca": "Banca organizadora",
    "localidade": "Palmas - TO",
    "status": "Edital publicado",
    "inscricoes_inicio": "2026-11-12",
    "inscricoes_fim": "2026-12-10",
    "data_prova": "2027-02-21",
    "url_edital": "",
    "url_oficial": "",
    "observacoes": "A prova discursiva será aplicada no mesmo dia.",
    "prioridade": false,
    "cargos": [
      {
        "nome": "Médico",
        "nivel_escolaridade": "Superior",
        "requisitos": "Graduação em Medicina e registro ativo no CRM",
        "salario_inicial": "R$ 12.000,00",
        "salario_final": "",
        "beneficios": "Auxílio alimentação",
        "jornada": "20 horas semanais",
        "vagas": "3",
        "localidade": "Palmas - TO",
        "observacoes": "Remuneração proporcional à jornada"
      }
    ],
    "disciplinas": [
      {
        "nome": "Conhecimentos específicos",
        "topicos": [
          {
            "nome": "Políticas públicas de saúde",
            "nome_padronizado": ""
          }
        ]
      }
    ]
  }
}
~~~

Os valores permitidos para status são Sem Previsão, Previsto e Edital publicado. Use texto vazio quando um valor não estiver disponível. A lista de cargos pode ficar vazia quando nenhum cargo corresponder ao perfil ou quando o edital não detalhar cargos. Cada salário deve permanecer associado ao cargo correto. O conteúdo programático deve refletir os cargos incluídos.

## 5. Sobre a antiga Data prevista

O antigo campo **Data prevista** não distinguia com segurança uma data de prova confirmada de uma estimativa. Por isso, foi retirado da interface e do prompt. Atualmente, o sistema registra a **Data da prova** somente quando a fonte a informa. Concursos ainda sem data continuam podendo ser cadastrados como Previsto ou Sem Previsão.

A coluna antiga permanece apenas no esquema interno de bancos já existentes, para permitir a abertura de bases antigas sem migração destrutiva. Ela não é mais exibida, utilizada na ordenação ou exportada em novos backups. JSONs antigos com esse campo são aceitos por compatibilidade, mas seu valor é ignorado.

## 6. Conferência humana recomendada

A IA pode interpretar incorretamente tabelas, notas de rodapé, páginas digitalizadas ou retificações. A importação não substitui a conferência do edital. Antes de usar a ficha para planejar inscrições, confirme especialmente o cargo, os requisitos, a escolaridade, a jornada, as vagas, a remuneração, as datas, os links oficiais e os tópicos programáticos.

Não misture valores de remuneração de cargos diferentes. Confira também se o salário informado é mensal, por hora, por plantão ou condicionado a jornada, titulação ou gratificações.
