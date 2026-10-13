# Como editar vídeos com Claude · versão clara (9:16)

Motion explicativo PT-BR, recriado a partir de `Motion_PTBR_Roteiro_Prompts_v01.md` e do
storyboard `Storyboard_Claude_Claro_v01_APROVACAO.pdf`. 1080×1920, 30 fps, 46,5 s no total
(roteiro de 40 s com o ritmo ajustado à narração + assinatura JACK).

**Status:** v07 final: 13 cenas + assinatura, 46,5 s, com narração, legendas sincronizadas e efeitos.

- v01: prévia de 0–8 s; animações aprovadas.
- v02: composição escalada para ocupar o quadro vertical; logo em laranja e preto; cenas 05–13.
- v03: ritmo mais calmo; pausas depois das digitações e no fim de cada ação (40 → 50 s).
- v04: efeitos sonoros enviados para o projeto, sincronizados no pico de cada ação.
- v05: assinatura final com o lettering JACK animado como o intro de jackdsgn.github.io.
- v06: narração (ElevenLabs) posicionada por cena, legendas palavra a palavra e mix final em −16 LUFS.
- v07: pausas recalculadas pela narração (54,2 → 46,5 s): ~0,4–0,7 s entre uma fala e a próxima.

| Arquivo | O que é |
|---|---|
| `out/claude-video-v07-46s-final.mp4` | Vídeo final, 46,5 s, H.264 + AAC (voz + efeitos) |
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

## Assinatura final

Depois de "Crie com direção." (40,0 s no roteiro), a cena e o logo do canto saem e o lettering JACK
entra com a coreografia do intro do site (`jackTimeline` em `assets/js/site.js` de
jackdsgn.github.io), recalculada por quadro em vez de usar o GSAP:

1. K surge no centro girando de −180° a 0° e escalando de 0 a 1 (0,6 s, `back.out(1.7)`);
2. K desliza para o lugar (0,8 s, `expo.inOut`);
3. J, A e C sobem pela máscara (0,7 s cada, `expo.out`, intervalo de 0,13 s) e o JACK fica parado até o fim.

O JACK completo fica parado por ≈1,3 s. Mesmo SVG e mesma máscara do site, em Deep Blue `#202030` sobre o fundo claro, com 620 px de largura e
centro em y ≈ 860. Sons: whoosh no giro e no deslize, pops nas letras e clique no JACK completo.

## Ritmo

A timeline de `seek()` segue os tempos do roteiro (40 s). Antes dela, `PACE` ajusta o ritmo à
narração: `hold` congela um estado estável e `{a, b, len}` alonga ou encurta um trecho. A regra é
deixar ~0,4–0,7 s entre o fim da fala de uma cena e o começo da próxima, com duas exceções: o envio
do pedido (cena 08) só acontece depois de a fala terminar, e a cena 06 fica com ~1 s porque a fala é
curta para os materiais. Para mudar o ritmo, edite só `PACE`; `DURATION`, voz, legendas e efeitos
acompanham.

| Onde | Ajuste |
|---|---|
| 02 · o 7 assenta | +0,3 s |
| 04 · guia e referências | +0,8 s (a fala é mais longa que a cena) |
| 05 · SKILL.md digitado | +0,3 s |
| 06 · depois dos materiais | 0,9 s → 0,15 s |
| 07 · anexos | +0,8 s (a fala é mais longa que a cena) |
| 08 · antes do envio | +1,6 s, para a fala terminar antes do clique |
| 09 · check | +0,3 s |
| 10 · ajuste concluído | +0,6 s |
| 11 · resumo | 0,8 s → 1,2 s |
| 13 · tela final parada | 2,5 s → 1,0 s |

## Pipeline

```bash
npm install
node tools/stills.mjs /tmp/stills 1.0 3.6 5.6   # quadros avulsos
node tools/render.mjs                           # [início] [fim=DURATION] [fps=30] [sub=4] → frames/master.mkv
python3 audio/narracao.py                       # → audio/voz.wav, audio/legendas.js
python3 audio/sfx_mix.py                        # → audio/sfx.wav
python3 audio/mix.py                            # → audio/mix.wav (−16 LUFS)
tools/encode.sh claude-video-v07-46s-final audio/mix.wav   # → out/*.mp4
```

Para ver um quadro: `film.html?t=4.6`. Para tocar em tempo real: `film.html?play`.

## Pendências

- Frase final da narração ("Na hora de criar…"), se quiser fala na cena 13.
- Trilha licenciada e som de digitação (não veio entre os efeitos enviados).
