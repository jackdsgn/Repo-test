# Como editar vídeos com Claude · versão clara (9:16)

Motion explicativo PT-BR, recriado a partir de `Motion_PTBR_Roteiro_Prompts_v01.md` e do
storyboard `Storyboard_Claude_Claro_v01_APROVACAO.pdf`. 1080×1920, 30 fps, 54,2 s no total
(roteiro de 40 s + pausas de leitura + assinatura JACK).

**Status:** v06 final: 13 cenas + assinatura, 54,2 s, com narração, legendas sincronizadas e efeitos.

- v01: prévia de 0–8 s; animações aprovadas.
- v02: composição escalada para ocupar o quadro vertical; logo em laranja e preto; cenas 05–13.
- v03: ritmo mais calmo; pausas depois das digitações e no fim de cada ação (40 → 50 s).
- v04: efeitos sonoros enviados para o projeto, sincronizados no pico de cada ação.
- v05: assinatura final com o lettering JACK animado como o intro de jackdsgn.github.io.
- v06: narração (ElevenLabs) posicionada por cena, legendas palavra a palavra e mix final em −16 LUFS.

| Arquivo | O que é |
|---|---|
| `out/claude-video-v06-54s-final.mp4` | Vídeo final, 54,2 s, H.264 + AAC (voz + efeitos) |
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

Mesmo SVG e mesma máscara do site, em Deep Blue `#202030` sobre o fundo claro, com 620 px de largura e
centro em y ≈ 860. Sons: whoosh no giro e no deslize, pops nas letras e clique no JACK completo.

## Ritmo

A timeline de `seek()` segue os tempos do roteiro (40 s). Antes dela, `PACE` remapeia o tempo:
cada `hold` congela um estado estável depois que a ação termina (o cursor continua piscando) e o
`stretch` alonga o resumo. Para mudar o ritmo, edite só `PACE`; `DURATION` é recalculada.

| Onde | Pausa |
|---|---|
| 03 · chat pronto | +0,6 s |
| 04 · guia e referências | +0,8 s |
| 05 · SKILL.md digitado | +1,5 s |
| 06 · materiais | +0,8 s |
| 07 · anexos | +0,8 s |
| 08 · pedido digitado, antes do envio | +1,5 s |
| 08 · "Preparando a prévia…" | +1,0 s |
| 09 · check | +0,6 s |
| 10 · ajuste concluído | +1,2 s |
| 11 · resumo | 1 s → 2 s |

## Narração e legendas

`audio/narracao.mp3` (34,35 s) é cortada nas pausas pelo `silencedetect`: são 23 trechos de fala que
batem com o roteiro em ordem e em duração (5–7 sílabas/s). A frase final do roteiro ("Na hora de
criar, comece pelo roteiro e termine revisando cada cena.") não está no arquivo, então a cena 13 e a
assinatura ficam sem fala.

`audio/narracao.py` põe a fala de cada cena no início dela, mantendo as pausas internas, e gera
`audio/legendas.js`: o texto que a voz diz, em grupos de 2–6 palavras, com a palavra dita em terracota.
As bordas de cada trecho são medidas; dentro do trecho, o tempo de cada palavra é proporcional às
sílabas (não havia transcrição automática neste ambiente).

`audio/mix.py` soma voz e efeitos: efeitos 7 dB abaixo da voz, com ducking de 6 dB enquanto ela fala,
−16 LUFS integrado e true peak de −1,2 dBTP.

## Efeitos sonoros

`audio/sfx/` guarda os três arquivos enviados. Como não foi possível ouvi-los, a função de cada um
foi definida pela análise de envelope e espectro:

| Arquivo | Perfil | Uso |
|---|---|---|
| `pop-grave_495.mp3` | impacto curto e grave (96% < 200 Hz) | entrada de cards e painéis |
| `clique_503.mp3` | ataque seco e brilhante, pico em 0,84 s | envio, checks, o "7", o marcador |
| `whooshes_864.mp3` | 5 whooshes (picos em 0,10/1,05/2,67/4,78/6,43 s) | troca de cena, alternando os 5 |

`audio/sfx_mix.py` lê a lista `PACE` do `film.html` e põe o pico de cada som no momento visual da
ação (69 deixas, desvio medido ≤ 10 ms). Nas cascatas o tom sobe a cada item e o volume baixa.
O nível final dos efeitos é definido em `audio/mix.py`.

## Pipeline

```bash
npm install
node tools/stills.mjs /tmp/stills 1.0 3.6 5.6   # quadros avulsos
node tools/render.mjs                           # [início] [fim=DURATION] [fps=30] [sub=4] → frames/master.mkv
python3 audio/narracao.py                       # → audio/voz.wav, audio/legendas.js
python3 audio/sfx_mix.py                        # → audio/sfx.wav
python3 audio/mix.py                            # → audio/mix.wav (−16 LUFS)
tools/encode.sh claude-video-v06-54s-final audio/mix.wav   # → out/*.mp4
```

Para ver um quadro: `film.html?t=4.6`. Para tocar em tempo real: `film.html?play`.

## Pendências

- Frase final da narração ("Na hora de criar…"), se quiser fala na cena 13.
- Trilha licenciada e som de digitação (não veio entre os efeitos enviados).
