# Fixer Audio 2.0.0

Reconstrução em Qt 6 / PySide6 para Windows.

- Janela redimensionável com menus, dropdowns acessíveis por teclado, fontes embarcadas e ícone próprio.
- Fila em lote com drag-and-drop, remoção de itens, cancelamento e resultados por arquivo.
- Correção de áudio AMD ReLive para AAC estéreo, mantendo o vídeo.
- Limpeza de metadados de áudio e vídeo com cópia dos fluxos.
- Extração de áudio para FLAC, WAV ou MP3.
- Conversão para MP4 H.264 + AAC para compatibilidade com players comuns.
- Saídas com nomes únicos, pasta persistida e substituição de originais opcional na limpeza.
- Instalador por usuário com runtime incluído e desinstalador.
- Busca de atualizações na abertura, notificação discreta e download validado com SHA-256.

Validação: mídia real nos quatro modos, decodificação das saídas, hash dos fluxos na limpeza, cancelamento, dropdowns e fila em testes Qt, instalação/execução/desinstalação isoladas.

Baixe `FixerAudioAMD-Setup.exe`. Não requer Python nem código-fonte. O FFmpeg pode ser instalado pelo menu Ferramentas.
