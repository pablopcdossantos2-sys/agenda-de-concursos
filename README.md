# Agenda de Concursos

Aplicativo desktop portátil para Windows, desenvolvido em Python, para organizar concursos públicos, acompanhar datas, estruturar conteúdos programáticos e comparar editais.

## Funcionalidades

- Cadastro de concursos em qualquer fase: **Sem Previsão**, **Previsto** ou **Edital publicado**.
- Fichas com órgão, cargo, banca, localidade, datas, links e observações.
- Cadastro individual de disciplinas e tópicos de cada concurso.
- Campo de padronização opcional para associar tópicos equivalentes com nomes diferentes.
- Comparação explicável de dois conteúdos programáticos, por disciplina e por tópico.
- Widget de área de trabalho com quantidade de itens configurável.
- Opção para iniciar com o Windows, sem serviço ou registro permanente: o aplicativo cria um script na pasta Inicializar do usuário.
- Banco SQLite local e exportação/importação de backup JSON.
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
pyinstaller --noconfirm --clean --windowed --name "Agenda de Concursos" --onedir main.py
~~~

Copie a pasta dist/Agenda de Concursos para o local desejado. Extraia-a em uma pasta na qual o usuário tenha permissão de escrita (evite diretórios protegidos do Windows). Na primeira execução, o aplicativo cria data/agenda.db. Mantenha a pasta data junto do programa ao movê-lo para outro computador. Se a inicialização automática estiver habilitada, desabilite-a antes de mover a pasta e habilite novamente depois, pois o script da pasta Inicializar aponta para o caminho atual do executável.

## Dados e privacidade

Os dados são armazenados localmente em SQLite. O aplicativo não envia fichas ou conteúdos para servidores. Faça backups periódicos pelo menu **Configurações**. O backup JSON contém fichas, disciplinas, tópicos e preferências do aplicativo.

A opção de inicialização do Windows grava/remover um script .vbs na pasta Inicializar do usuário atual. Ela não altera serviços ou chaves de registro.

## Como interpretar a comparação

A comparação é uma estimativa textual, não uma avaliação oficial de equivalência de editais. Ela considera:
- coincidência de nomes de disciplinas após normalização;
- semelhança lexical dos tópicos;
- chaves de padronização preenchidas pelo usuário, que representam correspondência explícita.

O relatório mostra a cobertura por disciplina e os tópicos correspondentes. Revise os pares sugeridos antes de usar o resultado para decidir seu planejamento de estudos.

## Estrutura

- main.py: ponto de entrada.
- agenda/database.py: persistência SQLite e backup.
- agenda/services/similarity.py: comparação dos conteúdos.
- agenda/startup.py: integração opcional com a pasta Inicializar do Windows.
- agenda/ui/: janela principal, diálogos, tema e widget.
- tests/: testes automatizados.

## Estado do projeto

Primeira versão funcional em desenvolvimento. O comportamento de janela-widget, inicialização e empacotamento precisa ser validado em Windows real antes de ser considerado pronto para distribuição.
