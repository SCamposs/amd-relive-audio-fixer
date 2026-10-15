# Fixer de Áudio AMD ReLive

Utilitário simples para Windows que corrige clipes gravados pelo AMD ReLive que abrem sem som em players comuns por causa da faixa de áudio multicanal 7.1.

O vídeo é mantido sem recodificação e apenas o áudio é convertido para AAC estéreo (2 canais). Fiz esta ferramenta para corrigir meus clipes rapidamente, sem precisar abri-los sempre em players específicos para HEVC.

## Como usar

1. Baixe e abra `FixerAudioAMD.exe`.
2. Selecione o clipe `.mp4` com problema.
3. Escolha onde salvar e clique em **Corrigir áudio para estéreo**.

O FFmpeg precisa estar instalado no Windows ou o arquivo `ffmpeg.exe` deve ficar na mesma pasta do programa.
