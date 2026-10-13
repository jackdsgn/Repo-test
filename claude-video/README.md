# Como editar vídeos com Claude · versão clara (9:16)

Motion explicativo PT-BR, recriado a partir de `Motion_PTBR_Roteiro_Prompts_v01.md` e do
storyboard `Storyboard_Claude_Claro_v01_APROVACAO.pdf`. 1080×1920, 30 fps, 40 s no total.

**Status:** prévia de aprovação 0–8 s (cenas 01 a 03 completas e início da 04), **sem áudio**.
Cenas 05 a 13 entram depois da aprovação.

| Arquivo | O que é |
|---|---|
| `out/previa-v01-0-8s-SEM-AUDIO.mp4` | Prévia 0–8 s, H.264, faixa AAC silenciosa |
| `out/comparacao-storyboard-v01.png` | Storyboard × render nos mesmos instantes |
| `film.html` | Motor: `window.seek(t)` determinístico, todas as cenas em texto e vetor |

## Grade (do storyboard, Reels)

- Área útil x 90–910 / y 300–1240; composição centrada em x = 500 (170 px reservados à direita).
- Progresso de 7 segmentos em y 312, label "Passo n" e título à esquerda em x 170.
- Legenda centrada em y ≈ 1080, palavra ativa em terracota.
- Logo Jackdsgn claro (arquivo oficial do Design System) em x 108, y 1184, 150 px, estático.

Cores do briefing: fundo `#F7F4ED`, texto `#24231F`, terracota `#D77A5C`, linha `#DAD7CC`, cards `#FFFFFF`.
Fontes: Instrument Serif (candidata, não a fonte original da referência), Inter e JetBrains Mono, todas OFL, locais em `assets/`.

## Pipeline

```bash
npm install
node tools/stills.mjs /tmp/stills 1.0 3.6 5.6   # quadros avulsos
node tools/render.mjs 0 8 30 4                  # início, fim, fps, subquadros → frames/master.mkv
tools/encode.sh previa-v01-0-8s-SEM-AUDIO       # → out/*.mp4
```

Para ver um quadro: `film.html?t=4.6`. Para tocar em tempo real: `film.html?play`.

## Pendências

- Locução PT-BR gravada (os tempos de legenda e de ação são estimados até haver timestamps reais).
- Trilha licenciada e efeitos (digitação, entrada de cards, envio, conclusão).
