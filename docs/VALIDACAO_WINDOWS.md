# Validação prática no Windows

Esta lista deve ser executada em um computador com Windows 10 ou 11 antes de distribuir o aplicativo a outras pessoas.

## 1. Execução pelo código-fonte

1. Instale Python 3.10 ou superior.
2. Extraia uma cópia limpa do repositório.
3. Abra PowerShell na pasta do projeto.
4. Execute:
   ~~~powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   py main.py
   ~~~
5. Confirme que a janela abre sem mensagens de erro e que o ícone aparece na janela e na área de notificação quando disponível.

## 2. Perfil do usuário e prompt personalizado

1. Abra a seção **Perfil**.
2. Marque somente **Superior** e salve.
3. Informe Médico e Jornalista, um por linha, e salve novamente.
4. Abra **Prompts** e confira se o texto inclui o nível Superior e as profissões Médico e Jornalista.
5. Confirme que o prompt exige que nível e profissão sejam atendidos simultaneamente e que solicita cargos vazios quando não houver correspondência.
6. Remova os cargos desejados, deixe todos os níveis desmarcados e salve.
7. Abra novamente **Prompts** e confirme que não há filtro de nível ou profissão, isto é, todos os cargos do edital devem ser considerados.
8. Feche e reabra o aplicativo; confirme que o perfil foi preservado.

## 3. Fluxo de cadastro e cargos

1. Crie uma ficha com situação **Sem Previsão**, sem datas.
2. Crie outra ficha com situação **Previsto** e informe uma data de prova.
3. Crie uma ficha com situação **Edital publicado**.
4. Em **Cargos e salários**, cadastre pelo menos dois cargos com níveis, requisitos, remunerações, benefícios, jornada e vagas diferentes.
5. Edite uma ficha, altere um cargo e confirme que os outros cargos não foram modificados.
6. Confirme que não existe mais o campo **Data prevista** e que um concurso sem data pode continuar cadastrado.
7. Exclua uma ficha de teste e confirme a solicitação de confirmação.

## 4. Datas e conteúdo programático

1. Preencha datas no formulário usando DD/MM/AAAA, por exemplo 12/11/2026.
2. Salve, reabra a ficha e confirme que o valor continua correto.
3. Confira que cartões, tabela e ficha completa apresentam a data por extenso, por exemplo **12 de Novembro de 2026**.
4. Cadastre duas ou mais disciplinas e tópicos individualmente.
5. Edite um tópico e preencha o nome padronizado.
6. Feche e reabra o programa; confirme que datas, disciplinas e tópicos foram preservados.

## 5. Agenda de datas e ficha completa

1. Cadastre concursos com e sem datas, incluindo ao menos um com inscrições, data de prova, banca, links, observações em várias linhas e conteúdo programático.
2. Na tela **Visão geral**, confirme que todos os concursos são apresentados em cards, inclusive os sem data de prova.
3. Clique em cada card e confira se a janela de detalhes apresenta informações gerais, calendário, links, cargos e salários, observações, disciplinas e tópicos.
4. Clique em **Abrir edital** e **Abrir site oficial**. Teste endereços com e sem o prefixo https:// e confirme que o navegador abre o destino correto.
5. Se um endereço for inválido, confira se o aplicativo apresenta uma mensagem compreensível e não falha silenciosamente.
6. Confira que as observações aparecem separadas em blocos ou itens legíveis, sem formar um único parágrafo extenso.
7. Na subseção **Cargos e salários**, edite, adicione e remova um cargo; confirme que a ficha e os cards refletem a alteração.

## 6. Widget e bandeja do Windows

1. Abra o widget usando **Mostrar widget** na barra de ferramentas.
2. Confirme que início das inscrições, fim das inscrições e data da prova aparecem em linhas separadas.
3. Na ficha, abra **Gerenciar cargos e salários**, selecione um cargo, clique em **Marcar como de interesse** e em **Concluir**. Confira o destaque na ficha e a linha com nome e remuneração no widget.
4. Marque vários cargos e confira que é possível ler os nomes e as remunerações. Passe o ponteiro sobre o título do card para ler o texto completo.
5. Em **Configurações**, altere quantidade de cards, largura (320–700 px) e altura (300–900 px), salve e confirme as dimensões.
6. Reduza a altura e confira se a rolagem vertical permite ler os cards que excedem o espaço disponível.
7. Use **Ocultar widget** na barra de ferramentas da janela principal e depois **Mostrar widget**.
8. Clique com o botão direito no ícone do Agenda de Concursos na área de notificação do Windows e teste **Mostrar/Ocultar widget**.
9. Feche a janela principal pelo X. Confirme que ela é minimizada para a bandeja e que o menu do ícone permite reabri-la e sair do aplicativo.
10. Reinicie o aplicativo e confirme que quantidade, largura e altura permanecem salvas.

## 7. Temas, contraste e superfícies

1. Teste o **Modo claro** e o **Modo escuro**.
2. Em ambos, confirme a legibilidade de Agenda, texto de versão, títulos dos painéis, botões, campos, tabelas, cards, cargos e janela de detalhes.
3. Verifique que rótulos dentro de painéis não exibem retângulos com cores de fundo diferentes da superfície do painel.
4. Confirme que a tabela, os diálogos, o widget, a bandeja e a barra de ferramentas seguem o tema selecionado.
5. Verifique contraste e corte de textos com escala de tela de 100%, 125% e 150%.

## 8. Links, observações e navegação

1. Cadastre um link de edital com protocolo HTTPS e outro sem protocolo.
2. Tente abrir ambos na subseção **Links e fontes**.
3. Cadastre observações com linhas iniciadas por tópicos e linhas no formato título: descrição.
4. Confira a organização da subseção **Observações** e a legibilidade em ambos os temas.
5. Navegue por todas as seções, inclusive Perfil e Prompts, e confirme que nenhum conteúdo fica oculto ou ilegível.

## 9. Inicialização automática

1. Em uma instalação nova, abra o aplicativo e confirme que o widget aparece e a janela principal pode ser aberta pela bandeja.
2. Em **Configurações** da Agenda, abra as configurações de inicialização do Windows e habilite o aplicativo.
3. Reinicie a sessão e confira se o widget e o ícone da bandeja aparecem com a janela principal fechada.
4. Desabilite o aplicativo na lista de inicialização do Windows e confira o comportamento no próximo logon.

## 10. Backup e migração

1. Cadastre perfil, cargos, salários, disciplinas e tópicos.
2. Exporte o backup JSON.
3. Altere ou remova dados de teste e importe o backup anterior.
4. Confirme que perfil, cargos, salários, disciplinas e tópicos voltaram ao momento da exportação.
5. Confira que o backup novo não contém o antigo campo Data prevista.
6. Importe um backup da edição portátil na edição instalada e confira se os dados foram restaurados.

## 11. Validar a distribuição

Gere e instale o MSIX conforme o [guia de publicação](PUBLICACAO_MICROSOFT_STORE.md) e repita os testes pelo menu Iniciar do Windows. Abra outro aplicativo sobre o widget e verifique que a nova janela pode cobri-lo.

## Resultado da validação

Registre data, versão do Windows, arquitetura, resolução/escala de tela, versão do Python (se aplicável), resultado de cada etapa, mensagens de erro e evidências. Não marque como validado aquilo que não foi testado em Windows real.
