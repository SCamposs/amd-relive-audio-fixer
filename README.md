# Fixer de Áudio AMD ReLive

Utilitário simples para Windows que corrige clipes gravados pelo AMD ReLive que abrem sem som em players comuns por causa da faixa de áudio multicanal 7.1. Também remove metadados incorporados de arquivos de áudio sem recodificar o conteúdo.

O vídeo é mantido sem recodificação e apenas o áudio é convertido para AAC estéreo (2 canais). Fiz esta ferramenta para corrigir meus clipes rapidamente, sem precisar abri-los sempre em players específicos para HEVC.

## Corrigir áudio do AMD ReLive

1. Baixe e abra `FixerAudioAMD.exe`.
2. Na primeira execução, permita que o app baixe o FFmpeg caso ele ainda não esteja disponível.
3. Selecione o clipe `.mp4` com problema.
4. Escolha onde salvar e clique em **Corrigir áudio para estéreo**.

## Remover metadados

1. Abra a aba **Limpar metadados**.
2. Selecione um ou mais arquivos de áudio.
3. Clique em **Remover metadados** e confirme.

A limpeza sobrescreve os próprios arquivos, sem criar backup. O áudio não é recodificado, portanto não há perda de qualidade.

## FFmpeg

O app oferece o download automático do FFmpeg na primeira execução. Se preferir instalar manualmente, use uma destas opções:

```powershell
winget install --id Gyan.FFmpeg.Essentials --exact
```

```powershell
choco install ffmpeg
```

```powershell
scoop install ffmpeg-essentials
```

Também é possível baixar uma versão para Windows pela [página oficial do FFmpeg](https://ffmpeg.org/download.html#build-windows) e deixar `ffmpeg.exe` ao lado do programa. A mesma instalação é usada tanto para corrigir os clipes quanto para limpar os metadados.
