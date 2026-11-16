# Fixer Audio 3

App para Windows para corrigir o áudio de clipes AMD ReLive e preparar arquivos de mídia em lote. Interface React + Base UI, com topbar própria, drag-and-drop, dropdowns, cancelamento, resultados por arquivo e instalação por usuário.

- Correção 7.1 para AAC estéreo, mantendo o vídeo.
- Limpeza de metadados de áudio e vídeo sem recodificação.
- Extração da primeira faixa de áudio para FLAC, WAV ou MP3.
- Conversão para MP4 H.264 + AAC para players comuns.

FLAC/WAV não usam compressão com perdas; MP3 e a conversão H.264 recodificam o conteúdo. As saídas recebem nomes únicos. Na limpeza, é possível optar por substituir o original após o processamento terminar.

O vídeo é mantido sem recodificação e apenas o áudio é convertido para AAC estéreo (2 canais). Fiz esta ferramenta para corrigir meus clipes rapidamente, sem precisar abri-los sempre em players específicos para HEVC.

## Corrigir áudio do AMD ReLive

1. Baixe e execute `FixerAudioAMD-Setup.exe` na página de [Releases](https://github.com/SCamposs/amd-relive-audio-fixer/releases).
2. No menu Ferramentas, instale o FFmpeg caso ele ainda não esteja disponível.
3. Selecione o clipe `.mp4` com problema.
4. Escolha **Corrigir áudio**, a pasta de saída e clique em **Processar fila**.

## Remover metadados

1. Escolha **Limpar metadados** no dropdown de operações.
2. Selecione um ou mais arquivos de áudio ou vídeo.
3. Clique em **Processar fila**. Confirme caso tenha marcado a opção de substituir originais.

A limpeza cria uma cópia por padrão. A opção de substituir originais exige confirmação e não cria backup. Os fluxos de áudio e vídeo não são recodificados.

## Atualizações

O app consulta a versão mais recente no GitHub sempre que é aberto. Quando há uma atualização, uma bolinha aparece na barra de título; clique nela para baixar e abrir o novo instalador.

## FFmpeg

O app oferece o download do FFmpeg pelo menu Ferramentas. Se preferir instalar manualmente, use uma destas opções:

```powershell
winget install --id Gyan.FFmpeg.Essentials --exact
```

```powershell
choco install ffmpeg
```

```powershell
scoop install ffmpeg-essentials
```

Também é possível baixar uma versão para Windows pela [página oficial do FFmpeg](https://ffmpeg.org/download.html#build-windows) e disponibilizar `ffmpeg.exe` no PATH. A mesma instalação é usada tanto para corrigir os clipes quanto para limpar os metadados.

## Desenvolvimento

Python 3.12 e Node.js 22. Crie `.venv`, instale `requirements.txt` e `pyinstaller`, execute `npm ci --prefix frontend` e `npm run build --prefix frontend`, depois `python corretor_audio.py`. Para compilar o instalador, instale Inno Setup 6 e execute `build.ps1`.

O instalador inclui Python e a interface; usuários não precisam do código-fonte ou do Node.js. Requer Windows 10/11 com [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/), normalmente já instalado no Windows. Créditos e licenças em `THIRD_PARTY.md` e `licenses/`.
