# Publicação na Microsoft Store

1. Reserve o nome do aplicativo no Partner Center. Na página **Identidade do produto**, copie **Package/Identity/Name**, **Package/Identity/Publisher** e **Package/Properties/PublisherDisplayName**.
2. Em Windows x64, instale o Windows SDK com MakeAppx e execute os comandos abaixo. Use os três valores do Partner Center e escolha uma versão superior à da última submissão.

   ```powershell
   py -m pip install -r requirements.txt pyinstaller
   py packaging/build_msix.py `
     --package-name "<Package/Identity/Name>" `
     --publisher "<Package/Identity/Publisher>" `
     --publisher-display-name "<Package/Properties/PublisherDisplayName>" `
     --version 1.0.0.0
   ```

3. Valide a edição instalada com o [roteiro de Windows](VALIDACAO_WINDOWS.md). Para testar fora da loja, assine o pacote com um certificado confiável no dispositivo de teste. A Store assina o MSIX após a certificação.
4. Envie `dist/AgendaDeConcursos.msix` pelo Partner Center com a descrição, capturas de tela, classificação indicativa e um URL público para a [política de privacidade](PRIVACIDADE.md). Justifique a capacidade `runFullTrust` como necessária para executar o aplicativo desktop Qt com janela flutuante e ícone da bandeja. Revise as condições de redistribuição das dependências Qt/PySide6 da versão final.

O pacote de validação do GitHub Actions usa uma identidade de teste. Para submissão, gere outro MSIX com os valores do produto no Partner Center.

A inicialização é habilitada pelo usuário em **Configurações > Aplicativos > Inicialização** do Windows. O banco SQLite fica no armazenamento local do usuário. Para migrar da edição portátil, use a exportação e a importação de backup JSON.

[Checklist de preparação da Microsoft Store](https://learn.microsoft.com/en-us/windows/apps/publish/store-readiness-checklist) · [Políticas da Microsoft Store](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies)
