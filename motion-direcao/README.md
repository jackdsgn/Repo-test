# Motion com direção · Do termo ao prompt (9:16)

Motion explicativo PT-BR feito a partir de `Storyboard_Motion_com_Direcao_v01_APROVACAO.pdf`:
7 cenas, 1080×1920, 30 fps. Mesmo motor do `claude-video/`: textos e formas em camadas, quadro
calculado por `window.seek(t)`, render em Chrome headless.

**Status:** v01 completo, 55 s, com narração, efeitos e legendas em `.srt`.

| Arquivo | O que é |
|---|---|
| `out/motion-com-direcao-v01-55s.mp4` | Vídeo, H.264 + AAC (voz + efeitos), −16 LUFS |
| `out/legendas.srt` | Legendas da narração, 34 linhas de 2–5 palavras |
| `film.html` | Motor e cenas |
| `audio/narracao.mp3` | Narração (ElevenLabs, 54,05 s) |
| `audio/narracao.py` | Corta a narração em trechos e calcula o tempo de cada palavra → `audio/palavras.json`, `out/legendas.srt` |
| `audio/sfx_mix.py`, `audio/mix.py` | Efeitos (os mesmos aprovados no vídeo anterior) e mixagem final |

## Duração e sincronia

O storyboard prevê 60 s. A narração gravada tem 54 s e segue a ordem e o ritmo do roteiro, então a
voz fica contínua, sem cortes, e as cenas acompanham a fala (55 s no total). Cada demonstração
acontece quando o termo é dito:

| Cena | Início | Ação ancorada na fala |
|---|---|---|
| 01 Hook | 0,0 s | a interrogação sai em "Dê direção" |
| 02 Entradas | 4,6 s | fade in em "Fade in" (6,2 s), slide in em "Slide in" (8,9 s), stagger em "Stagger" (10,8 s) |
| 03 Ritmo | 13,85 s | o 1º percurso começa em "Ease in-out" (15,85 s) e dura 2,5 s; corte didático; repetição |
| 04 Texto | 22,6 s | palavras em "revele palavras" (23,45 s), contagem em "contagem" (26,25 s), faixa em "destaque" (27,45 s) |
| 05 Transições | 29,8 s | morph de "transforme" a "morph" (31,15–32,95 s), wipe em "ou revele a próxima com wipe" (33,8 s) |
| 06 Prompt | 37,3 s | uma linha por parâmetro dito; prévia com fade de 0,5 s e 2 s imóvel; sublinhados em "elemento", "ação", "tempo" |
| 07 Salvar | 49,0 s | marcador, quatro chips, "Crie com direção." e logo; tela parada até 55 s |

A ordem dentro da cena 04 segue a voz (contagem antes da faixa), não a ficha.

## Grade e identidade

- As cenas são desenhadas nas coordenadas dos frames do storyboard (941×1672) dentro de `#content`,
  escalado em 1,02× e centralizado: tudo cabe na área segura pedida (x 90–990, y 180–1600).
- Tokens do storyboard: marfim `#F8F5EF`, carvão `#242320`, coral `#D88467`; cards `#FCFAF7`.
- Títulos em Instrument Serif com a palavra-chave em itálico coral; apoio em Inter.
- Onde o frame e a ficha divergem, vale a ficha: rastros e setas dos frames são notação, então cada
  efeito mostra um único objeto; a paisagem do wipe virou formas abstratas.
- Continuidade entre cenas, como pede a ficha: o quadrado coral vira o card do Fade in; dois cards
  viram as pistas; a pista inferior vira o sublinhado e depois a faixa de "ideia"; a faixa vira o
  quadrado do morph; o wipe ocupa o quadro e revela a cena 06.
- Logo: lockup oficial laranja e preto do Design System, pequeno e estável, só na cena 07.

## Áudio

- Narração contínua desde 0 s; efeitos 7 dB abaixo, com ducking de 6 dB enquanto a voz fala.
- Efeitos nos pontos da ficha: pulso de abertura, clique do pedido, pop do quadrado, whoosh da
  expansão, um tick por exemplo, whoosh no 1º percurso (a repetição fica sem som), som no fim da
  contagem, whoosh no wipe final (sem som no morph), clique ao iniciar a prévia e pop no marcador.
- Mix final: −16 LUFS integrado, true peak abaixo de −1 dBTP.
- Legendas em `.srt` em vez de gravadas na imagem: o storyboard pede para não sobrepor legendas aos
  rótulos das demonstrações, e a área de baixo já tem as frases de apoio.

## Pipeline

```bash
npm install
python3 audio/narracao.py                      # → audio/palavras.json, out/legendas.srt
python3 audio/sfx_mix.py && python3 audio/mix.py   # → audio/sfx.wav, audio/mix.wav
node tools/render.mjs                          # → frames/master.mkv (55 s)
tools/encode.sh motion-com-direcao-v01-55s audio/mix.wav
```

Para ver um quadro: `film.html?t=27.6`. Para tocar em tempo real (sem áudio): `film.html?play`.

## Pendências

- Trilha instrumental com licença (o storyboard pede trilha discreta sob a voz).
