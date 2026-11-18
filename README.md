# Agenda de Concursos

Aplicativo desktop para Windows, desenvolvido em Python, para organizar concursos públicos, acompanhar datas, estruturar conteúdos programáticos e comparar editais.

## Funcionalidades

- Cadastro de concursos em qualquer fase: **Sem Previsão**, **Previsto** ou **Edital publicado**.
- Fichas com órgão, banca, localidade, datas, links e observações.
- Cadastro de vários cargos por concurso, com marcação individual de interesse e destaque para a remuneração na ficha e no widget.
- Seção **Perfil** para selecionar níveis de escolaridade, profissões e requisitos adicionais desejados.
- Seção **Prompts** que gera instruções de extração personalizadas pelo perfil salvo, para filtrar cargos de editais em PDF ou imagens.
- Cadastro por formulário convencional ou por JSON validado, incluindo cargos, salários, disciplinas e tópicos.
- Datas apresentadas em português por extenso; os campos editáveis aceitam DD/MM/AAAA e o banco mantém ISO AAAA-MM-DD.
- Cadastro individual de disciplinas e tópicos de cada concurso.
- Comparação explicável de dois conteúdos programáticos, por disciplina e por tópico.
- Widget flutuante com início e fim das inscrições, data da prova e remuneração dos cargos de interesse em linhas separadas. A rolagem vertical aparece quando o conteúdo ultrapassa a altura configurada.
- Mostrar/ocultar widget pela barra de ferramentas da janela principal ou pelo menu do ícone na área de notificação do Windows.
- Ícone próprio do aplicativo, incluindo a bandeja do sistema.
- Tema claro (padrão) e tema escuro, com paletas e textos de alto contraste.
- O widget abre na área de trabalho, e a janela principal fica acessível pelo botão **Abrir Agenda** e pelo ícone da bandeja. A edição MSIX pode iniciar com o Windows quando o usuário a habilita nas configurações do sistema.
- Banco SQLite local e exportação/importação de backup JSON, incluindo perfil e cargos.
- Funciona offline para as funcionalidades locais.

## Requisitos

- Windows 10 ou 11 (64 bits).
- Python 3.10 ou superior para execução pelo código-fonte.
- PySide6.

## Executar pelo código-fonte

1. Instale Python 3.10+.
2. Abra o terminal na pasta do projeto.
3. Crie um ambiente virtual (opcional, recomendado):
   ~~~powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ~~~
4. Instale as dependências:
   ~~~powershell
   py -m pip install -r requirements.txt
   ~~~
5. Inicie:
   ~~~powershell
   py main.py
   ~~~

## Distribuição pela Microsoft Store

O GitHub Actions gera um MSIX x64 com identidade de validação. Para gerar o pacote de publicação com a identidade reservada, siga o [guia de publicação](docs/PUBLICACAO_MICROSOFT_STORE.md).

Para migrar da edição portátil, exporte um backup JSON no aplicativo antigo e importe-o em **Configurações** na edição instalada. Desative a inicialização automática na edição antiga antes de substituí-la.

## Dados e privacidade

Os dados ficam no armazenamento local do usuário do Windows, fora da pasta do executável. O backup JSON exportado em **Configurações** inclui fichas, cargos, disciplinas, tópicos e preferências. [Política de privacidade](docs/PRIVACIDADE.md)

## Como interpretar a comparação

A comparação é uma estimativa textual, não uma avaliação oficial de equivalência de editais. Ela considera:
- coincidência de nomes de disciplinas após normalização;
- semelhança lexical dos tópicos;
- chaves de padronização preenchidas pelo usuário, que representam correspondência explícita.

O relatório mostra a cobertura por disciplina e os tópicos correspondentes. Revise os pares sugeridos antes de usar o resultado para decidir seu planejamento de estudos.

## Estrutura

- main.py: ponto de entrada.
- agenda/database.py: persistência SQLite, perfil, cargos e backup.
- agenda/services/dates.py: normalização e apresentação das datas.
- agenda/services/profile.py: normalização do perfil.
- agenda/services/contest_payload.py: validação do formato JSON de cadastro.
- agenda/services/prompts.py: prompt de extração personalizado.
- agenda/services/similarity.py: comparação dos conteúdos.
- packaging/: manifesto e geração do MSIX.
- agenda/ui/: janela principal, perfil, cards clicáveis, ficha detalhada, gestão de cargos, temas, importação por JSON e widget.
- assets/app_icon.svg: ícone vetorial próprio do aplicativo.
- docs/IMPORTACAO_JSON_E_PROMPTS.md: guia de perfil, seção Prompts e importação.
- tests/: testes automatizados.

## Estado do projeto

Versão funcional em desenvolvimento. O comportamento de janela-widget, bandeja, inicialização e empacotamento deve continuar sendo validado em Windows real antes de uma distribuição ampla.
