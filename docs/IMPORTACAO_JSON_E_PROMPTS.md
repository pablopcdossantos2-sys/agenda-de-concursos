# Cadastro por código JSON e seção Prompts

O aplicativo oferece duas formas de criar uma ficha de concurso:

1. **Formulário convencional**: preenchimento manual dos campos.
2. **Inserção por código JSON**: colagem de uma ficha estruturada, inclusive produzida por uma IA a partir de um edital ou de imagens.

A inserção por código aceita exclusivamente JSON validado. O aplicativo **não executa Python, comandos ou scripts** recebidos de terceiros.

## Como usar a seção Prompts

1. Abra **Prompts** na navegação lateral ou na barra de ferramentas.
2. Copie o prompt apresentado na janela.
3. Em uma ferramenta de IA que aceite arquivos, anexe o edital em PDF ou as imagens com as informações do concurso.
4. Cole o prompt e peça à IA para retornar somente o JSON no formato solicitado.
5. Leia o resultado, confira nomes, datas, banca, cargo e conteúdo programático com o documento original.
6. Copie o JSON produzido pela IA.

## Como importar o JSON

1. Abra **Concursos** e escolha **Inserir por código JSON**.
2. Apague o exemplo que aparece no editor e cole o JSON.
3. Clique em **Validar e adicionar**.
4. Se houver erro, leia a mensagem indicada, corrija o JSON e tente novamente.
5. Após a validação, a ficha e as disciplinas/tópicos são gravados em uma única transação no SQLite.
6. Confira os dados na lista de concursos e na seção **Conteúdo programático**.

## Estrutura aceita

O objeto JSON deve conter schema_version igual a 1 e um objeto concurso. O nome do concurso é obrigatório. Datas devem usar AAAA-MM-DD; campos desconhecidos são rejeitados para evitar importações silenciosamente incorretas.

~~~json
{
  "schema_version": 1,
  "concurso": {
    "nome": "Concurso de exemplo",
    "orgao": "Órgão público",
    "cargo": "Cargo ou especialidade",
    "banca": "",
    "localidade": "",
    "status": "Previsto",
    "inscricoes_inicio": "",
    "inscricoes_fim": "",
    "data_prova": "",
    "data_prevista": "",
    "url_edital": "",
    "url_oficial": "",
    "observacoes": "",
    "prioridade": false,
    "disciplinas": [
      {
        "nome": "Língua Portuguesa",
        "topicos": [
          {
            "nome": "Compreensão e interpretação de textos",
            "nome_padronizado": ""
          }
        ]
      }
    ]
  }
}
~~~

Os valores permitidos para status são Sem Previsão, Previsto e Edital publicado. Use texto vazio quando uma informação textual ou data estiver ausente; disciplinas pode ser uma lista vazia quando o edital não apresentar o conteúdo programático.

## Conferência humana recomendada

A IA pode interpretar incorretamente tabelas, notas de rodapé, páginas digitalizadas ou datas retificadas. A importação não substitui a conferência do edital. Antes de usar a ficha para planejar inscrições, confirme especialmente as datas, os links oficiais, os requisitos do cargo e todos os tópicos programáticos.
