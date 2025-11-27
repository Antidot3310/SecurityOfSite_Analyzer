# ARCHITECTURE (черновой)

## Цель документа
Краткое описание структуры проекта и ответственности основных модулей.

---

## Краткое описание
Scanner-MVP — минималистичный прототип сканера уязвимостей веб-форм. На текущем этапе реализован локальный парсер форм и базовый HTTP-утилит (`fetch_info`). Проект ориентирован на MVP: извлечение форм из HTML, сохранение результатов и покрытие тестами.

---

## Компоненты / модули
- `src/extractor.py`
  - `fetch_html(target: str) -> str` — получает HTML из `file://` или HTTP/HTTPS.
  - `extract_forms(html: str) -> List[Form]` — парсит HTML, возвращает объекты `Form` и `InputField`.
  - Модели: `Form` (action, method, inputs), `InputField` (name, type, value).
  - Сохраняет результаты в `results.json` (MVP).

- `src/exercise1.py`
  - Учебное: парсинг строк CSV -> словари.

- `src/exercise2.py`
  - `fetch_info(target: str) -> dict` — надёжный HTTP / локальный файл helper, возвращает `{url, status, length, ok, error}`.

- `src/app.py` (планируется)
  - Flask-приложение с endpoint `/api/parse?url=...` для вызова `extractor` и получения JSON-отчёта.

- `src/storage/` (планируется)
  - Интерфейс для сохранения результатов (SQLite). В MVP можно хранить JSON; позже — sqlite + simple schema.

- `tests/`
  - Unit-тесты: `test_extractor.py`, `test_fetch_info.py`, `test_exercise1.py`.
  - Тесты запускаются через `pytest`.

---

## Поток данных (data flow)
1. Вход: `target` (локальный файл `file://...` или URL).
2. `fetch_html` получает HTML.
3. `extract_forms` превращает HTML в объекты `Form`.
4. Результат сериализуется в JSON (`results.json`) и/или возвращается через HTTP API.
5. Дополнительно: тесты проверяют корректность поведения функций.

---

## Параметры запуска / dev
- Виртуальное окружение: `python -m venv venv`
- Установка зависимостей: `pip install -r requirements.txt`
- Локальный запуск extractor:  
  `python src/extractor.py file://./src/sample1.html`
- Тесты: `pytest -q`

---

## Ограничения и допущения (MVP)
- Не сканировать чужие сайты без разрешения.
- На MVP не поддерживается парсинг JS-динамически сгенерированных форм (Selenium/Playwright — в будущих итерациях).
- Хранение результатов — JSON (позже — SQLite).

---

## Планы на ближайшее развитие
1. Интегрировать `extractor` в Flask (`/api/parse`).
2. Добавить `src/storage` (SQLite) и базовую схему.
3. Добавить CI (GitHub Actions) для автозапуска `pytest`.
4. Добавить базовый rule-based scanner (SQLi/XSS) и позже ML-компонент.

---
