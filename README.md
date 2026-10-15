# Fixer de Áudio AMD ReLive

Utilitário simples para Windows que corrige clipes gravados pelo AMD ReLive que abrem sem som em players comuns por causa da faixa de áudio multicanal 7.1.

O vídeo é mantido sem recodificação e apenas o áudio é convertido para AAC estéreo (2 canais). Fiz esta ferramenta para corrigir meus clipes rapidamente, sem precisar abri-los sempre em players específicos para HEVC.

## Como usar

1. Baixe e abra `FixerAudioAMD.exe`.
2. Na primeira execução, permita que o app baixe o FFmpeg caso ele ainda não esteja disponível.
3. Selecione o clipe `.mp4` com problema.
4. Escolha onde salvar e clique em **Corrigir áudio para estéreo**.

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

Também é possível baixar uma versão para Windows pela [página oficial do FFmpeg](https://ffmpeg.org/download.html#build-windows) e deixar `ffmpeg.exe` ao lado do programa.
