# Scanner-MVP — прототип сканера уязвимостей веб-форм (MVP)

Кратко
------
Минималистичный прототип для курсовой: извлекает формы из HTML и содержит базовые утилиты для работы с HTTP и локальными файлами. 
Проект в начальной стадии (Day1–Day2).

Текущее состояние (на момент README)
------------------------------------
- Сделано: окружение, VS Code, git (Day 1).
- Сделано: учебные упражнения `exercise1.py` и `exercise2.py` (Day 2, базовые парсинг/HTTP).
- В процессе/запланировано: `extractor.py` (парсер форм в объектную модель), `ARCHITECTURE.md`, unit-тесты и интеграция в Flask.

Структура (ожидаемая)
---------------------
/repo
/src
exercise1.py # CSV-парсер (учебное упражнение)
exercise2.py # fetch_info (HTTP + локальные файлы)
extractor.py # (будет) парсер форм -> объекты Form/InputField
sample1.html # тестовый локальный HTML
/tests
test_exercise1.py
test_fetch_info.py
test_extractor.py
requirements.txt
README.md
ARCHITECTURE.md # (будет) краткая архитектура модулей