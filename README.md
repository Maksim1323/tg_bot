# Telegram Bot: Перевод + OCR + Передача заданий

Бот с тремя режимами работы:

1. **Перевод текста** (English → Russian) + PDF из 3 страниц (оригинал / перевод / как читать русскими буквами)
2. **OCR** — распознавание текста с фото + PDF
3. **Произвольное задание** — описание + файлы отправляются администратору

## Быстрый старт (локально)

### 1. Клонируй репозиторий

```bash
git clone https://github.com/ТВОЙ_ЮЗЕРНЕЙМ/tg-translate-ocr-bot.git
cd tg-translate-ocr-bot
```

### 2. Создай виртуальное окружение и установи зависимости

```bash
python -m venv venv
source venv/bin/activate          # Linux / macOS
# или
venv\Scripts\activate             # Windows

pip install -r requirements.txt
```

> **Важно:** EasyOCR скачивает модели (~100–200 МБ) при первом запуске. Это нормально.

### 3. Настрой переменные окружения

Создай файл `.env` в корне проекта:

```env
BOT_TOKEN=1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
ADMIN_ID=123456789
```

Как получить:
- `BOT_TOKEN` — создай бота у [@BotFather](https://t.me/BotFather)
- `ADMIN_ID` — узнай свой ID через [@userinfobot](https://t.me/userinfobot) или [@getmyid_bot](https://t.me/getmyid_bot)

### 4. Запусти

```bash
python bot.py
```

Напиши боту `/start` в Telegram.

---

## Как сделать так, чтобы бот работал 24/7 (даже когда компьютер выключен)

Нужно запустить бота на **сервере**, который работает постоянно.

### Вариант 1: Railway.app (самый простой, есть бесплатный тариф)

1. Зарегистрируйся на [railway.app](https://railway.app)
2. Нажми **New Project → Deploy from GitHub repo**
3. Подключи свой GitHub-репозиторий
4. В настройках сервиса добавь **Variables**:
   - `BOT_TOKEN` = твой токен
   - `ADMIN_ID` = твой user_id
5. В **Settings → Deploy** укажи:
   - Start Command: `python bot.py`
6. Railway сам установит зависимости из `requirements.txt` и запустит бота.

Готово. Бот будет работать постоянно.

### Вариант 2: Render.com

1. Зарегистрируйся на [render.com](https://render.com)
2. **New → Web Service**
3. Подключи GitHub-репозиторий
4. Настройки:
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
5. Добавь Environment Variables (`BOT_TOKEN`, `ADMIN_ID`)
6. Deploy

> Бесплатный план "засыпает" после 15 минут бездействия. Для Telegram-бота это не критично (бот проснётся при первом сообщении), но лучше взять платный или использовать Railway/Fly.io.

### Вариант 3: VPS (Timeweb, Selectel, DigitalOcean, Contabo и т.д.)

Самый надёжный способ.

```bash
# На сервере (Ubuntu)
sudo apt update
sudo apt install python3-pip python3-venv git -y

git clone https://github.com/ТВОЙ_ЮЗЕРНЕЙМ/tg-translate-ocr-bot.git
cd tg-translate-ocr-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Создай .env
nano .env
# вставь BOT_TOKEN и ADMIN_ID

# Запуск через screen (простой способ)
screen -S bot
python bot.py
# Ctrl+A+D чтобы отключиться

# Или через systemd (рекомендуется)
```

Пример systemd-сервиса (`/etc/systemd/system/tgbot.service`):

```ini
[Unit]
Description=Telegram Translate OCR Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/tg-translate-ocr-bot
ExecStart=/root/tg-translate-ocr-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable tgbot
sudo systemctl start tgbot
sudo systemctl status tgbot
```

### Вариант 4: PythonAnywhere (бесплатно, но с ограничениями)

Подходит для лёгких ботов. EasyOCR может не влезть в бесплатный тариф из-за размера моделей.

---

## Структура проекта

```
tg_bot/
├── bot.py                 # Основной файл бота
├── config.py              # Настройки
├── states.py              # FSM-состояния
├── requirements.txt
├── README.md
├── .env.example
└── services/
    ├── translator.py      # Перевод + фонетика
    ├── ocr.py             # Распознавание текста
    └── pdf_generator.py   # Генерация PDF
```

## Команды бота

| Команда   | Описание                          |
|-----------|-----------------------------------|
| `/start`  | Главное меню                      |
| `/cancel` | Отменить текущее действие         |
| `/help`   | Справка                           |
| `/done`   | Завершить отправку файлов в режиме задания |

## Важные замечания

- **EasyOCR** при первом запуске скачивает модели. На слабом сервере это может занять время и память.
- Для кириллицы в PDF в продакшене лучше добавить шрифт `DejaVuSans.ttf`.
- Поиск похожих изображений пока не реализован полноценно (нужен внешний API).
- Не выкладывай `.env` и токен в публичный репозиторий!

## Лицензия

MIT
