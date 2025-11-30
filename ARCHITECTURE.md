# ARCHITECTURE (черновой)

## Компоненты / модули
- `src/extractor.py`
  - `fetch_html(target: str) -> str` — получает HTML из `file://` или HTTP/HTTPS.
  - `extract_forms(html: str) -> List[Form]` — парсит HTML, возвращает объекты `Form` и `InputField`.
  - Модели: `Form` (action, method, inputs), `InputField` (name, type, value).
  - Сохраняет результаты в `results.json` (MVP).

- `src/parse_line.py`
  - Учебное: парсинг строк CSV -> словари.

- `src/parse.py`
  - `fetch_info(target: str) -> dict` — надёжный HTTP / локальный файл helper, возвращает `{url, status, length, ok, error}`.

- `src/app.py`
  - Flask-приложение с endpoint `/api/parse?url=...` для вызова `extractor` и получения JSON-отчёта.

- `src/storage/` (планируется)
  - Интерфейс для сохранения результатов (SQLite). В MVP можно хранить JSON; позже — sqlite + simple schema.

- `tests/`
  - Unit-тесты: `test_extractor.py`, `test_parse.py`, `test_parse_line.py`, `test_app.py`
  - Тесты запускаются через `pytest`.

---

## Поток данных (data flow)
1. Вход: `target` (локальный файл `file://...` или URL).
2. `fetch_html` получает HTML.
3. `extract_forms` превращает HTML в объекты `Form`.
4. Результат сериализуется в JSON (`results.json`) и/или возвращается через HTTP API.

---

## Параметры запуска / dev
- Виртуальное окружение: `python -m venv venv`
- Установка зависимостей: `pip install -r requirements.txt`
- Локальный запуск extractor:  
  `python src/extractor.py file://./src/sample1.html`
- Тесты: `pytest -q`
