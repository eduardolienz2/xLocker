# xLocker

O xLocker é um aplicativo para Windows que reúne um cofre local de senhas e um gerador de senhas. Ele foi feito para ajudar você a criar credenciais fortes e guardá-las protegidas no seu próprio computador. Seus dados não são enviados nem sincronizados com um servidor do xLocker.

## O que você pode fazer

- Criar senhas aleatórias e ajustar o comprimento e os tipos de caracteres.
- Evitar caracteres que podem ser confundidos, como `O` e `0` ou `l` e `1`.
- Consultar a estimativa de entropia da senha gerada.
- Salvar senhas, nomes de sites e usuários no cofre local.
- Pesquisar registros, revelar ou ocultar senhas e copiar usuário ou senha.
- Bloquear o cofre manualmente ou deixar que ele seja bloqueado após um período sem atividade.

## Como começar

1. Baixe o pacote para Windows na [release mais recente](https://github.com/eduardolienz2/xLocker/releases/latest).
2. Extraia **todos** os arquivos do ZIP para uma pasta. Mantenha os arquivos juntos; não execute o `.exe` diretamente de dentro do ZIP.
3. Abra `xLocker.exe`.
4. No primeiro uso, crie e confirme uma senha mestra com pelo menos 12 caracteres. Nos próximos usos, informe essa senha para abrir o cofre.
5. Na aba **Generator**, ajuste o comprimento e as opções e gere uma senha. Informe um site ou aplicativo e, se quiser, um usuário; use **Save to vault** para guardar a senha no cofre.
6. Na aba **Vault**, pesquise os registros e use as ações disponíveis para mostrar, copiar ou excluir uma entrada. Use **Lock** para bloquear o cofre ao terminar.

**A senha mestra não pode ser recuperada.** Se você esquecê-la, o xLocker não poderá abrir o cofre.

## Proteja seus dados

- Escolha uma senha mestra longa, única e difícil de adivinhar. Não a reutilize em outros serviços nem a compartilhe.
- Faça cópias de segurança regulares do arquivo do cofre e guarde-as em um local seguro, separado do computador. Uma cópia do arquivo não substitui a senha mestra.
- O arquivo do cofre fica em `%APPDATA%\SecureVault\vault.dat`. Ele é criptografado, mas mantenha os backups protegidos e apague-os com cuidado quando não forem mais necessários.
- Bloqueie o cofre quando se afastar. O aplicativo também o bloqueia automaticamente após três minutos sem atividade.
- Senhas copiadas para a área de transferência são apagadas após 30 segundos quando o conteúdo ainda é o que o xLocker copiou. Evite copiar senhas em computadores compartilhados ou comprometidos.
- Mantenha o Windows atualizado, use bloqueio de tela e proteja o dispositivo contra acesso não autorizado.
- O cofre é local: o xLocker não oferece sincronização nem recuperação de conta. Planeje como manter e proteger seus backups.

## Dados técnicos

- **Sistema:** Windows.
- **Armazenamento:** `%APPDATA%\SecureVault\vault.dat`; os registros são criptografados localmente com AES-256-GCM.
- **Proteção da chave:** derivação a partir da senha mestra com scrypt (`N=131072`, `r=8`, `p=1`).
- **Gerador:** usa o gerador criptográfico seguro do sistema operacional; a interface oferece comprimentos de 8 a 64 caracteres.
- **Executável:** pacote PyInstaller no modo `onedir`; extraia o ZIP completo antes de executar.
- **Código-fonte:** requer Python 3.10 ou superior. Para executar a partir do código, instale as dependências e inicie o app:

  ```powershell
  python -m pip install -r requirements.txt
  python app.py
  ```

- **Build no Windows:** execute `build.bat`. O script gera o aplicativo em `dist\xLocker` e o instalador; a etapa do instalador requer o Inno Setup 6.
