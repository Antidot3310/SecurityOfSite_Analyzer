# ARCHITECTURE (черновой)

## Цель
Коротко: минималистичный прототип сканера веб-форм (MVP).

## Структура проекта / основные модули
- `src/app.py`
  - Flask-приложение.
  - Вспомогательные функции:
    - `parse_forms_from_url(url: str) -> dict` — обёртка: получает HTML, парсит формы, возвращает словарь с `forms`, `html_length`, `forms_count`.
    - `save_to_file(data, filename)` — простая сериализация результатов.

- `src/extractor.py`
  - `fetch_html(url: str) -> Optional[str]` — получает HTML из src/fetcher.py/fetch_info.
  - `extract_forms(html: str, base_url: Optional[str]) -> List[Form]` — парсит HTML и возвращает объекты `Form`.
  - Модели (в `src/models.py`):
    - `Form` — `action`, `method`, `inputs`, `form_id`, `classes`, `enctype`.
    - `InputField` — `name`, `field_type`, `value`, `required`, `placeholder`, `meta`.
  - `parse_form_inputs(form_tag)` — собирает input/textarea/select, пропуская кнопки/submit.

- `src/fetcher.py`
  - `fetch_info(url: str, timeout: int = 5) -> dict` — универсальный helper для получения содержимого:
    - поддерживает `http`, `https` (requests) и `file` (локальное чтение).
    - возвращает структуру `{ url, status, length, ok, error, text }`.
  - `fetch_local_file(path)` и `fetch_web(url, timeout)` как разделение ответственности.

- `src/storage/db.py`
  - Работа с SQLite:
    - `init_db(path: Optional[str])` — создаёт таблицу `scans`.
    - `save_scan(target, results_json, meta, path)` — сохраняет запись, возвращает `id`.
    - `get_scan(id, path)` — получение записи.

- `src/scanner/` (опционально, следующий этап)
  - `scanner.py` — логика сканера: построение baseline, инъекция payload, сбор снимков ответов.
  - `detectors.py` — набор детекторов (reflection, sql error, time delay).
  - `payloads.py` + `types.py` — загрузка payloads, модели payload.

- `tests/`
  - Unit и интеграционные тесты (pytest):
    - `test_fetcher.py` — fetcher: file/http/errors.
    - `test_extractor.py` — парсер форм, чтение HTML.
    - `test_app_db.py` — один компактный интеграционный тест для `/api/parse` + DB.
    - `test_scanner.py`, `test_detectors.py` — для scanner (когда будет добавлен).

## Поток данных (data flow)
1. Вход: `target` — строка с URL или `file://` URI (через API или CLI).
2. `app.api_parse` получает параметр `url` и вызывает `parse_forms_from_url(url)`.
3. `parse_forms_from_url`:
   - вызывает `fetch_html(url)` — получает строку HTML или `None`.
   - вызывает `extract_forms(html, base_url)` — получает список `Form` объектов.
   - собирает результат: `{"forms": [...], "html_length": N, "forms_count": M}`.
4. `app`:
   - сериализует результат в БД через `save_scan(...)`,
   - пишет копию `forms` в `tests/test_data/Result.json` (MVP),
   - возвращает JSON ответ с `count`, `scan_id`, `forms`, `response_size`, `status_code`.

## DB схема (scans)
- Поля:
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `target` TEXT NOT NULL
  - `timestamp` TEXT NOT NULL (ISO)
  - `results_json` TEXT NOT NULL
  - `count` INTEGER NULL
  - `status_code` INTEGER NULL
  - `response_size` INTEGER NULL

## Короткие указания
- Запуск тестов: `pytest -q`
- Запуск dev-сервера: `python -m src.app`

