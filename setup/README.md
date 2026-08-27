# Окружение

```bash
sudo apt-get install -y ffmpeg libcairo2-dev libpango1.0-dev pkg-config \
                        python3-dev fonts-inter fonts-jetbrains-mono
sudo cp fonts-local.conf /etc/fonts/local.conf && fc-cache -f

python3 -m venv .venv
.venv/bin/pip install --upgrade pip setuptools wheel
.venv/bin/pip install manim python-pptx fonttools
```

`fonts-local.conf` задаёт цепочку подстановки шрифтов. Inter и JetBrains Mono
не покрывают весь юникод формул: в моно нет `ᵢ`, `⁻`, `ˣ`, `⟹`, в Inter —
`ᵀ`, `ℝ`, `↦`, `∈`, `⌊`, `⌋`. Без этого файла Pango подставляет растровые
unifont/ipag, и подстрочные индексы в формулах выглядят чужеродно.

Отдельно: на Debian/Ubuntu пропатченный `setuptools` ломает сборку `srt`
(зависимость manim) при установке в системный python — отсюда venv.
