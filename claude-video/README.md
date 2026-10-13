# Como editar vídeos com Claude · versão clara (9:16)

Motion explicativo PT-BR, recriado a partir de `Motion_PTBR_Roteiro_Prompts_v01.md` e do
storyboard `Storyboard_Claude_Claro_v01_APROVACAO.pdf`. 1080×1920, 30 fps, 40 s no total.

**Status:** v02 com as 13 cenas (0–40 s), **sem áudio**. A v01 (prévia de 0–8 s) teve as animações
aprovadas, com dois ajustes: composição escalada para ocupar o quadro vertical e logo em laranja e preto.

| Arquivo | O que é |
|---|---|
| `out/claude-video-v02-40s-SEM-AUDIO.mp4` | Vídeo completo, 40 s, H.264, faixa AAC silenciosa |
| `out/comparacao-storyboard-v02.png` | Storyboard (em cima) × render (embaixo), um quadro por cena |
| `film.html` | Motor: `window.seek(t)` determinístico, todas as cenas em texto e vetor |

## Grade

- As cenas são desenhadas nas coordenadas do storyboard (coluna centrada em x = 500, área y 300–1040)
  dentro de `#content`, escalado em 1,4× para ocupar o quadro: margem lateral de 72 px, progresso em
  y 275 e ilustração até y ≈ 1310.
- Legenda centrada em y ≈ 1400, 42 px, palavra ativa em terracota.
- Logo Jackdsgn horizontal, símbolo Vivid Orange `#F75C03` e JACK Deep Blue `#202030`, em x 72, y 1492, 180 px, estático.
- Os ~370 px inferiores ficam livres para a interface do Reels.

Cores do briefing: fundo `#F7F4ED`, texto `#24231F`, terracota `#D77A5C`, linha `#DAD7CC`, cards `#FFFFFF`.
Fontes: Instrument Serif (candidata, não a fonte original da referência), Inter e JetBrains Mono, todas OFL, locais em `assets/`.

## Pipeline

```bash
npm install
node tools/stills.mjs /tmp/stills 1.0 3.6 5.6   # quadros avulsos
node tools/render.mjs 0 40 30 4                 # início, fim, fps, subquadros → frames/master.mkv
tools/encode.sh claude-video-v02-40s-SEM-AUDIO  # → out/*.mp4
```

Para ver um quadro: `film.html?t=4.6`. Para tocar em tempo real: `film.html?play`.

## Pendências

- Locução PT-BR gravada (os tempos de legenda e de ação são estimados até haver timestamps reais).
- Trilha licenciada e efeitos (digitação, entrada de cards, envio, conclusão).
