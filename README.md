# Система управління студентами

Навчальний вебзастосунок для обліку студентів, груп, дисциплін і оцінок.
Наскрізний проєкт дисципліни «Технології проєктування та розробки мережевих ресурсів».

## Автор

Бондарчук Валерія, група КНІТ-63М

## Технології

- Python 3.13 або новіший, менеджер проєкту uv
- Django, Django REST Framework
- FastAPI
- Vue.js
- PostgreSQL (продакшен), SQLite (розробка), Docker, Docker Compose

## Запуск

Потрібен менеджер проєктів [uv](https://docs.astral.sh/uv/).

~~~bash
uv sync                 # створити середовище і встановити залежності
uv run student-portal   # запустити консольний застосунок
~~~

Змінна середовища `LOG_LEVEL` задає рівень журналу (`DEBUG`, `INFO`, `WARNING`,
`ERROR`); за замовчуванням виводяться лише попередження. З рівнем `INFO`
декоратор `@timed` показує час збереження, імпорту і розсилки:

~~~bash
LOG_LEVEL=INFO uv run student-portal                      # Linux, macOS
$env:LOG_LEVEL="INFO"; uv run student-portal              # PowerShell
~~~

## Журнал оцінок

Пункт меню 9 імпортує оцінки з файлу CSV у кодуванні UTF-8 з роздільником `;`
(так його зберігає Excel з українськими регіональними налаштуваннями).
Перший рядок - заголовок, далі одна оцінка на рядок:

~~~csv
student_id;course;score;graded_on
1;Вебтехнології;91;2026-10-20
~~~

Імпорт працює за правилом «все або нічого»: якщо хоча б один рядок має
неправильний формат або посилається на неіснуючого студента, жодну оцінку
з файлу не буде додано, а меню покаже номер рядка з помилкою. Приклади:
`data/journal.csv` і `data/journal-broken.csv`.

## Сервер деканату

Пункт меню 11 завантажує групу у форматі `group.json` із сервера деканату і
пропонує замінити нею поточну. Адресу задає змінна середовища `DEKANAT_URL`
(за замовчуванням `https://dekanat.example.edu/api/groups/kn-11`). Якщо сервер
недоступний, не відповів за 5 с або повернув дані в неправильному форматі,
меню показує помилку і продовжує роботу.

Для ручної перевірки роздайте файл даних локальним вебсервером:

~~~bash
uv run python -m http.server 8001 -d data                                # перший термінал
DEKANAT_URL=http://127.0.0.1:8001/group.json uv run student-portal       # Linux, macOS
$env:DEKANAT_URL="http://127.0.0.1:8001/group.json"; uv run student-portal  # PowerShell
~~~

## Тести

Модульні тести pytest лежать у теці `tests/`, спільні фікстури - у `tests/conftest.py`.

~~~bash
uv run pytest                 # усі тести, короткий звіт
uv run pytest -v              # кожен тест окремим рядком
uv run pytest -k journal      # лише тести, у назві яких є «journal»
~~~

Тести працюють із файлами лише у тимчасовій теці (`tmp_path`) і не змінюють `data/`.
Мережу (`urlopen`), затримки розсилки і `input()` підміняють дублери, тож тести
не звертаються до сервера і нічого не чекають.

## Покриття і CI

Покриття рахується з розгалуженнями; поріг - 90 % (`[tool.coverage]` у
`pyproject.toml`), нижче нього `pytest --cov` завершується помилкою.

~~~bash
uv run pytest --cov                          # звіт у терміналі з непокритими рядками
uv run pytest --cov --cov-report=html        # HTML-звіт у htmlcov/index.html
~~~

На кожен pull request і push у `main` GitHub Actions (`.github/workflows/ci.yml`)
запускає два завдання: `checks` (Ruff і mypy) і `tests` (pytest з покриттям,
HTML-звіт зберігається як артефакт `coverage-html`). Правило гілки `main`
дозволяє злиття лише після зелених `checks` і `tests`.

## Перевірки

~~~bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
~~~

## Планування

Задачі та їхній статус ведуться на дошці GitHub Projects.
