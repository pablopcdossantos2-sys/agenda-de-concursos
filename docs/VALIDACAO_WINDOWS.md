# Validação prática no Windows

Esta lista deve ser executada em um computador com Windows 10 ou 11 antes de distribuir o aplicativo a outras pessoas.

## 1. Execução pelo código-fonte

1. Instale Python 3.10 ou superior.
2. Extraia/clique em uma cópia limpa do repositório.
3. Abra PowerShell na pasta do projeto.
4. Execute:
   ~~~powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   py main.py
   ~~~
5. Confirme que a janela abre sem mensagens de erro.

## 2. Fluxo de cadastro

1. Crie um concurso com situação **Sem Previsão**, sem datas.
2. Crie outro com situação **Previsto** e informe uma data prevista futura.
3. Crie um terceiro com situação **Edital publicado**, informando cargo, banca e links.
4. Edite uma ficha, salve e confirme que os dados permanecem após fechar e reabrir o programa.
5. Exclua uma ficha de teste e confirme a solicitação de confirmação.

## 3. Conteúdo programático

1. Selecione um concurso.
2. Cadastre duas ou mais disciplinas.
3. Cadastre tópicos individualmente dentro de cada disciplina.
4. Edite um tópico e preencha o nome padronizado.
5. Feche e reabra o programa; confirme que disciplinas e tópicos foram preservados.

## 4. Comparação

1. Cadastre dois concursos de teste com ao menos uma disciplina comum.
2. Insira tópicos idênticos, tópicos escritos de modo semelhante e tópicos exclusivos.
3. Repita um tópico com descrições diferentes, mas com o mesmo nome padronizado nos dois concursos.
4. Compare os dois concursos.
5. Confira a pontuação, os pares sugeridos e os tópicos exclusivos.
6. Confirme que a tela explica que o resultado é uma estimativa e exige revisão humana.

## 5. Widget

1. Abra **Mostrar widget**.
2. Confirme que a janela compacta lista somente eventos com data de hoje ou futura.
3. Altere a quantidade de itens nas Configurações e salve.
4. Oculte e mostre novamente o widget.
5. Com outras janelas abertas, confira se o widget permanece acessível e se não impede o uso do desktop.
6. Verifique posicionamento, legibilidade e escala em diferentes resoluções e fatores de escala do Windows.

## 6. Inicialização automática

1. Marque a opção de iniciar com o Windows e salve.
2. Abra a pasta Inicializar do usuário: pressione Win+R, digite **shell:startup** e confirme.
3. Verifique se existe o arquivo **Agenda de Concursos.vbs**.
4. Reinicie a sessão ou o computador e confira se o aplicativo abre.
5. Desmarque a opção e salve; confirme que o script foi removido.

## 7. Backup e portabilidade

1. Exporte o backup JSON.
2. Cadastre um dado de teste adicional.
3. Importe o backup anterior e confirme que o estado voltou ao momento da exportação.
4. Faça uma cópia da pasta distribuída para outro diretório gravável.
5. Execute a cópia e confirme que o banco de dados usado é o que está na pasta data da cópia.
6. Nunca apague o banco original antes de confirmar que o backup pode ser importado.

## 8. Gerar a distribuição

Na pasta do projeto, execute:

~~~powershell
py -m pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name "Agenda de Concursos" --onedir main.py
~~~

Copie a pasta dist\Agenda de Concursos para outro local. Execute o aplicativo nessa pasta e repita os testes de cadastro, widget, inicialização e backup.

## Resultado da validação

Registre data, versão do Windows, arquitetura, resolução/escala de tela, versão do Python (se aplicável), resultado de cada etapa, mensagens de erro e evidências. Não marque como validado aquilo que não foi testado em Windows real.
