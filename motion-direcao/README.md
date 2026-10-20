# Motion com direção · Do termo ao prompt (9:16)

Motion explicativo PT-BR feito a partir de `Storyboard_Motion_com_Direcao_v01_APROVACAO.pdf`:
7 cenas, 60 s, 1080×1920, 30 fps. Mesmo motor do `claude-video/`: textos e formas em camadas,
quadro calculado por `window.seek(t)`, render em Chrome headless.

**Status:** prévia v01 das cenas 01 e 02 (0–14 s), com efeitos sonoros e **sem locução**.
As cenas 03 a 07 entram depois da aprovação.

| Arquivo | O que é |
|---|---|
| `out/previa-v01-0-14s-cenas-01-02.mp4` | Prévia 0–14 s, H.264 + AAC (efeitos) |
| `film.html` | Motor e cenas |
| `audio/sfx_mix.py` | Efeitos sincronizados (mesmos sons aprovados no vídeo anterior) |

## Grade e identidade

- As cenas são desenhadas nas coordenadas dos frames do storyboard (941×1672) dentro de `#content`,
  escalado em 1,02× e centralizado: assim tudo cabe na área segura pedida (x 90–990, y 180–1600).
- Tokens do storyboard: marfim `#F8F5EF`, carvão `#242320`, coral `#D88467`; cards `#FCFAF7`.
- Títulos em Instrument Serif com a palavra-chave em itálico coral; apoio em Inter (fontes a definir
  pelo storyboard; mantive as do vídeo anterior).
- Onde o frame e a ficha divergem, vale a ficha: os rastros e setas dos frames são notação de
  trajetória, então cada efeito mostra um único objeto.

## Cenas 01–02 (prévia)

| Tempo | Ação |
|---|---|
| 0,0–0,5 s | Título legível desde o primeiro quadro; só "direção?" passa a coral |
| 0,5–1,4 s | Card "Faça algo dinâmico" sobe 24 px com fade |
| 1,3–1,9 s | Linha coral desce e o quadrado com "?" surge em 0,4 s |
| 3,7–4,6 s | A interrogação sai por opacidade |
| 4,6–5,4 s | O mesmo quadrado expande até virar o card do Fade in, sem reiniciar escala |
| 5,6–6,2 s | Fade in: um quadrado vai de 0 a 100% em 0,6 s |
| 7,7–8,35 s | Slide in: desliza 140 px da esquerda em 0,65 s, ease-out |
| 10,0–10,7 s | Stagger: três cards sobem 24 px com fade, 0,4 s cada, defasados 0,15 s |
| 13,5–14,0 s | Os dois primeiros contêineres viram as pistas da cena 03; o terceiro some |

Efeitos: pulso no início, clique ao mostrar o pedido, pop no quadrado, whoosh na expansão, um tick
por exemplo e whoosh suave na reorganização.

## Pipeline

```bash
npm install
node tools/stills.mjs /tmp/stills 3.0 12.6     # quadros avulsos
python3 audio/sfx_mix.py 14                    # → audio/sfx.wav
node tools/render.mjs 0 14                     # → frames/master.mkv
tools/encode.sh previa-v01-0-14s-cenas-01-02 audio/sfx.wav
```

## Pendências

- Locução PT-BR (roteiro na página 1 do storyboard) e trilha licenciada.
- Logo: o storyboard pede a assinatura original na cena 07; uso o lockup oficial laranja e preto
  do Design System, pequeno e estável.
