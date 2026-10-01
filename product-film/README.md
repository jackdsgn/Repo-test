# FIN JACK · Novo lançamento — product film (9:16)

Filme de UI motion de 24 s a 120 BPM, feito 100% em código a partir do Figma do FIN JACK.
Um container só, que nunca corta: cada estado é o mesmo elemento mudando tamanho, raio e preenchimento,
com o conteúdo trocando atrás de um blur curto. O cursor dispara todas as mudanças.

**Entregas:** `out/fin-jack-novo-lancamento-9x16.mp4` (H.264 + AAC) e `out/fin-jack-novo-lancamento-9x16.webm` (VP9 + Opus).
Ambas em 1080×1920, 60 fps, 24,000 s e −14 LUFS.

## História (12 compassos, 48 tempos)

| Comp. | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| **1** · 0 s | Hover no FJ | FJ se abre na **Home** | Indicadores entram | Hover no saldo |
| **2** · 2 s | Arrasta ↑ Previsibilidade + Fluxo | Barra 68% e barras do fluxo | Arrasta ↑ Contas + Movimentações | Contas entram |
| **3** · 4 s | Movimentações entram | Volta ao topo | Hover no **+** | Clique → **Novo lançamento** |
| **4** · 6 s | `8` · `6` | `4` · `0` → R$ 86,40 | Valor assenta | Clique "Selecionar ›" → lista |
| **5** · 8 s | Categorias em cascata | Hover em Moradia | Indicador estica até Alimentação | Clique → ✓ |
| **6** · 10 s | Lista → "Salvar lançamento · R$ 86,40" | Hover | Clique → loader | Arco fecha |
| **7** · 12 s | ✓ Toast "Lançamento salvo" | Check assenta | Clique → card Saldo | Odômetro rola |
| **8** · 14 s | R$ 4.733,95 assenta | "− R$ 86,40 · Alimentação" | Hover "Ver gastos" | Clique → gráfico |
| **9** · 16 s | Barras se desenham | S4 sobe em lime (214,30) | Hover → tooltip | "+ R$ 86,40 hoje" |
| **10** · 18 s | Clique "Previsão" → **Previsibilidade** | Dias 25–27 entram | Hover em entradas · dia 26 | Clique → R$ 1.500,00 |
| **11** · 20 s | Saldo do 26 sobe | Saldo do 27 sobe + "saldo projetado dia a dia" | Hover em **Home** | Clique (a bateria para) |
| **12** · 22 s | Lime cobre a tela + FJ | FIN JACK + slogan | segura | fim |

Os dados são os do Figma (dados demonstrativos, set/2026) e o filme mantém tudo coerente entre as telas:

- **Home:** saldo de R$ 4.820,35, indicadores e contas. Movimentações recentes aparecem sem "Supermercado", porque é o lançamento que o filme cria.
- **Despesa:** Supermercado · Alimentação · R$ 86,40. O saldo passa de R$ 4.820,35 para R$ 4.733,95 e o Diário de R$ 708,16 para R$ 794,56.
- **Previsibilidade:**
  - Dia 25 (hoje): o diário traz os R$ 86,40 e o saldo é R$ 4.733,95.
  - Dia 26: saídas de R$ 247,85 (valor do Figma). A receita prevista de R$ 1.500,00 entra nesse dia e leva o saldo de 26 e 27 de R$ 4.486,10 para R$ 5.986,10.
- **Assinatura:** a mesma da capa do Figma, "FIN JACK" com o slogan "Seu dinheiro, organizado do seu jeito.".

Tokens: canvas `#F7F7F6`, superfície `#FFFFFF`, muted `#F2F3F0`, texto `#111708` / `#6B7067`, acento único
lime `#AFF64E` (tint `#EAFBD8` em seleção e no dia de hoje), fonte Inter Tight. Verde e vermelho semânticos do Figma
ficam de fora para manter um acento só.

## Pipeline

```
audio/compose.py   trilha original 120 BPM, 12 compassos com final                     → track.wav
audio/analyze.py   librosa: andamento e fase nos compassos 1–6, cada beat no seu        → beats.json, timeline.json
                   transiente; tempo forte confirmado pela mudança de acorde
tools/inject.py    embute fonte + timeline medida no film.html (arquivo único)
audio/mix.py       sons de UI sintetizados nos picos medidos + ducking + −14 LUFS       → mix.wav
tools/render.mjs   Chrome headless, 60 fps × 4 subquadros, média = motion blur          → frames/master.mkv
tools/encode.sh    BT.709 → MP4 (H.264/AAC) e WebM (VP9/Opus)                           → out/
```

```bash
pip install numpy scipy librosa soundfile pyloudnorm pillow
npm install
python3 audio/compose.py && python3 audio/analyze.py && python3 tools/inject.py && python3 audio/mix.py
node tools/render.mjs && tools/encode.sh
node tools/stills.mjs /tmp/stills 1.6 10.6 21.0   # quadros avulsos para conferir
```

Para ver um quadro: abra `film.html?t=8.2`. Para tocar em tempo real (sem áudio): `film.html?play`.

## Como o motor funciona

- **`window.seek(t)` puro:** o quadro é função só do tempo. Não há CSS transitions, timers nem estado guardado entre seeks.
- **Springs em forma fechada:** cada valor é o valor inicial mais a soma de uma mola por mudança, `Δᵢ·S(t − tᵢ)`.
  ζ fica entre 0,78 e 0,95, o que dá overshoot de no máximo ~2 %.
- **Texto dentro do container:** entra 80 ms depois de o morph começar e sai 70 ms antes do próximo, sempre com blur.
- **Indicador da categoria:** a borda de ataque usa ω 21 e a de fuga ω 9, então ele estica.
- **Cores:** os preenchimentos interpolam em OKLab. Ao abrir para tela cheia, a cor corre mais rápido para não passar por cinza.
- **Câmera:** sem `will-change`, para o texto não borrar quando a câmera escala.
- **Fim:** a forma lime nasce do ícone Home (`clip-path: circle`) e cobre a tela. O cursor some e a câmera faz um push lento sobre a assinatura.
- **Música e UI:** a trilha abre espaço para a interface. Nos contratempos com clique, a palma cai para 30 %.
  No clique em Home, a bateria para por um tempo, e o acorde final resolve em Fá sob a logo.

Fonte Inter Tight © The Inter Tight Project Authors, SIL Open Font License 1.1 (Google Fonts).
