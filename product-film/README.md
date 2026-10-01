# FIN JACK · Novo lançamento — product film (9:16)

Filme de UI motion de 16 s em loop perfeito, a 120 BPM, feito 100% em código a partir do Figma do FIN JACK.
Um container só, que nunca corta: cada estado é o mesmo elemento mudando tamanho, raio e preenchimento,
com o conteúdo trocando atrás de um blur curto. O cursor dispara todas as mudanças.

**Entregas:** `out/fin-jack-novo-lancamento-9x16.mp4` (H.264 + AAC) e `out/fin-jack-novo-lancamento-9x16.webm` (VP9 + Opus).
Ambas em 1080×1920, 60 fps e 16,000 s, com o último quadro emendando no primeiro.

## História (12 estados, 32 tempos)

| Comp. | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| **1** · 0 s | Hover no FJ (lift) | FJ → pílula lime "+ Novo lançamento" | "+" gira · hover | Clique → campo de valor |
| **2** · 2 s | `8` · `6` (colcheias) | `4` · `0` → R$ 86,40 | Valor assenta | Clique "Selecionar ›" → lista |
| **3** · 4 s | Categorias em cascata | Hover em Moradia | Indicador estica até Alimentação | Clique → ✓ |
| **4** · 6 s | Lista → "Salvar lançamento · R$ 86,40" | Hover | Clique → loader | Arco fecha |
| **5** · 8 s | ✓ Toast "Lançamento salvo" | Check assenta | Clique → card Saldo | Odômetro rola |
| **6** · 10 s | R$ 4.733,95 assenta | "− R$ 86,40 · Alimentação" | Hover "Ver gastos" | Clique → gráfico |
| **7** · 12 s | Barras se desenham | S4 sobe em lime (214,30) | Hover → tooltip | "+ R$ 86,40 hoje" |
| **8** · 14 s | Clique "+" → botão | "+" gira de volta | Cursor sai → FJ | FJ assenta; cursor volta (= quadro 0) |

Dados reais do Figma (dados demonstrativos, set/2026): Supermercado · Alimentação · R$ 86,40; Saldo operacional
R$ 4.820,35 → R$ 4.733,95; Diário R$ 708,16 → R$ 794,56 (a divisão por semana S1–S4 foi proposta e aprovada).
Tokens do Figma: canvas `#F7F7F6`, superfície `#FFFFFF`, muted `#F2F3F0`, texto `#111708` / `#6B7067`,
acento único lime `#AFF64E` (tint `#EAFBD8` só na seleção), fonte Inter Tight.

## Pipeline

```
audio/compose.py   trilha original 120 BPM, 8 compassos, render circular (sem emenda)  → track_loop.wav
audio/analyze.py   librosa: beats, tempo forte (novidade de croma), picos              → beats.json, timeline.json
tools/inject.py    embute fonte + timeline medida no film.html (arquivo único)
audio/mix.py       sons de UI sintetizados nos picos medidos + ducking + −14 LUFS       → mix_loop.wav
tools/render.mjs   Chrome headless, 60 fps × 4 subquadros, média = motion blur          → frames/master.mkv
tools/encode.sh    BT.709 → MP4 (H.264/AAC) e WebM (VP9/Opus)                           → out/
```

```bash
pip install numpy scipy librosa soundfile pyloudnorm pillow
npm install
python3 audio/compose.py && python3 audio/analyze.py && python3 tools/inject.py && python3 audio/mix.py
node tools/render.mjs && tools/encode.sh
node tools/seamcheck.mjs        # cursor contínuo na emenda, seek(0) == seek(16)
```

Para ver um quadro: abra `film.html?t=8.2`. Para tocar em tempo real (sem áudio): `film.html?play`.

## Como o motor funciona

- **`window.seek(t)` puro:** o quadro é função só do tempo. Não há CSS transitions, timers nem estado guardado entre seeks.
- **Springs em forma fechada:** cada valor é uma base mais a soma de uma mola por mudança, `Δᵢ·S(t − tᵢ)`.
  Tudo é avaliado no círculo: as molas do loop anterior entram como `S − 1`, que vale zero quando assentam.
  Por isso posição e velocidade (do cursor inclusive) atravessam a emenda sem salto. ζ fica entre 0,82 e 0,95,
  o que dá overshoot de no máximo ~1 %.
- **Texto dentro do container:** entra 80 ms depois de o morph começar e sai 70 ms antes do próximo, sempre com blur.
- **Indicador da categoria:** a borda de ataque usa ω 21 e a de fuga ω 9, então ele estica.
- **Cores:** os preenchimentos interpolam em OKLab.
- **Câmera:** sem `will-change`, para o texto não borrar quando a câmera escala.
- **Música e UI:** a trilha abre espaço para a interface. Nos contratempos com clique, a palma cai para 30 % e o clique vira o backbeat.

Fonte Inter Tight © The Inter Tight Project Authors, SIL Open Font License 1.1 (Google Fonts).
