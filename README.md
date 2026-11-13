# Agenda de Concursos

Aplicativo desktop portátil para Windows, desenvolvido em Python, para organizar concursos públicos, acompanhar datas, estruturar conteúdos programáticos e comparar editais.

## Funcionalidades

- Cadastro de concursos em qualquer fase: **Sem Previsão**, **Previsto** ou **Edital publicado**.
- Fichas com órgão, banca, localidade, datas, links e observações.
- Cadastro de vários cargos por concurso, cada um com escolaridade, requisitos, remuneração inicial/final, benefícios, jornada, vagas e lotação.
- Seção **Perfil** para selecionar níveis de escolaridade, profissões e requisitos adicionais desejados.
- Seção **Prompts** que gera instruções de extração personalizadas pelo perfil salvo, para filtrar cargos de editais em PDF ou imagens.
- Cadastro por formulário convencional ou por JSON validado, incluindo cargos, salários, disciplinas e tópicos.
- Datas apresentadas em português por extenso; os campos editáveis aceitam DD/MM/AAAA e o banco mantém ISO AAAA-MM-DD.
- Cadastro individual de disciplinas e tópicos de cada concurso.
- Comparação explicável de dois conteúdos programáticos, por disciplina e por tópico.
- Widget flutuante de área de trabalho com cards, cantos arredondados e borda; quantidade, largura e altura configuráveis, sem botão interno ou barras de rolagem.
- Mostrar/ocultar widget pela barra de ferramentas da janela principal ou pelo menu do ícone na área de notificação do Windows.
- Ícone próprio do aplicativo, incluindo a bandeja do sistema.
- Tema claro (padrão) e tema escuro, com paletas e textos de alto contraste.
- Opção para iniciar com o Windows, sem serviço ou registro permanente: o aplicativo cria um script na pasta Inicializar do usuário.
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

## Distribuição portátil

A compilação recomendada é no modo **onedir**, e não onefile: o executável e suas bibliotecas ficam em uma pasta, enquanto o banco permanece em data/, ao lado do aplicativo. Para gerar:

~~~powershell
py -m pip install -r requirements.txt
py -m pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name "Agenda de Concursos" --onedir --add-data "assets;assets" main.py
~~~

Copie a pasta dist/Agenda de Concursos para o local desejado. Extraia-a em uma pasta na qual o usuário tenha permissão de escrita (evite diretórios protegidos do Windows). Na primeira execução, o aplicativo cria data/agenda.db. Mantenha a pasta data junto do programa ao movê-lo para outro computador. Com a bandeja do sistema disponível, fechar a janela principal a minimiza para a área de notificação; use o menu do ícone para mostrar/ocultar o widget ou sair do aplicativo.

## Dados e privacidade

Os dados são armazenados localmente em SQLite. O aplicativo não envia fichas, perfis ou conteúdos para servidores. Faça backups periódicos pelo menu **Configurações**. O backup JSON contém fichas, cargos, disciplinas, tópicos e preferências do aplicativo.

A opção de inicialização do Windows grava/remover um script .vbs na pasta Inicializar do usuário atual. Ela não altera serviços ou chaves de registro.

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
- agenda/startup.py: integração opcional com a pasta Inicializar do Windows.
- agenda/ui/: janela principal, perfil, cards clicáveis, ficha detalhada, gestão de cargos, temas, importação por JSON e widget.
- assets/app_icon.svg: ícone vetorial próprio do aplicativo.
- docs/IMPORTACAO_JSON_E_PROMPTS.md: guia de perfil, seção Prompts e importação.
- tests/: testes automatizados.

## Estado do projeto

Versão funcional em desenvolvimento. O comportamento de janela-widget, bandeja, inicialização e empacotamento deve continuar sendo validado em Windows real antes de uma distribuição ampla.
