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

## Вебзастосунок Django

Проєкт Django `config` і застосунок `students` використовують те саме ядро
`student_portal`, що й консольний застосунок, і показують ті самі дані.

Налаштування, які відрізняються між середовищами, беруться зі змінних середовища.
Скопіюйте `.env.example` у `.env` і вставте в нього новий ключ (файл `.env` не
комітять, він уже є в `.gitignore`):

~~~bash
cp .env.example .env
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
~~~

| Змінна | Значення | За замовчуванням |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | секретний ключ; ключ із символами `#` або `$` беруть в одинарні лапки | немає - без неї Django не запуститься |
| `DJANGO_DEBUG` | `1` вмикає режим налагодження | `0` (вимкнено) |
| `DJANGO_ALLOWED_HOSTS` | дозволені хости через пробіл, у лапках | порожньо |
| `DJANGO_READ_ONLY` | `1` вмикає режим лише для читання: POST, PUT, PATCH і DELETE отримують 503 | `0` (вимкнено) |

Команди запускають з файлом змінних:

~~~bash
uv run --env-file .env python manage.py migrate        # таблиці бази даних
uv run --env-file .env python manage.py load_group data/group.json
uv run --env-file .env python manage.py setup_roles    # групи «Викладачі» і «Деканат»
uv run --env-file .env python manage.py runserver      # http://127.0.0.1:8000/students/
uv run --env-file .env python manage.py group_stats data/group.json
uv run --env-file .env python manage.py debtors --course Python
~~~

Сторінки описано нижче, дані вони беруть з бази даних (див. «База даних і
адмінпанель»). Команда `load_group` переносить групу з файлу JSON у базу,
`group_stats` друкує кількість студентів і розподіл оцінок за шкалою ECTS,
`debtors` - боржників з дисциплінами заборгованості (параметр `--course` обмежує
однією дисципліною; шлях до файлу необов'язковий). Щоб не писати `--env-file`
щоразу, виконайте `export UV_ENV_FILE=.env` (bash/zsh) або
`$env:UV_ENV_FILE=".env"` (PowerShell).

### Сторінки

| Адреса | Що показує | Представлення |
| --- | --- | --- |
| `/students/` | список студентів з пошуком за прізвищем (`?q=`, `SearchForm`, до 50 символів) | `student_list` (FBV) |
| `/students/new/` | новий студент (право `add_student`) | `StudentCreateView` |
| `/students/<id>/` | картка студента: оцінки, середній бал, літера ECTS | `student_detail` (FBV) |
| `/students/<id>/edit/` | зміна студента (право `change_student`) | `StudentUpdateView` |
| `/students/<id>/grades/new/` | нова оцінка (право `add_grade`) | `add_grade` (FBV, `GradeForm`) |
| `/students/<id>.json` | дані студента у JSON | `student_json` (FBV) |
| `/students/ranking/` | рейтинг групи | `RankingView` (`TemplateView`) |
| `/students/pages/` | рейтинг по два студенти на сторінці (`?page=`) | `StudentListView` (`ListView`) |
| `/students/ects/<letter>/` | студенти із середнім балом на літеру ECTS (`A`…`E`, `Fx`) | `by_ects` (FBV, конвертер `ects`) |
| `/students/st/0003/` | стара адреса картки, перенаправлення 301 на `/students/3/` | `legacy_student` (`re_path`) |
| `/` | перенаправлення 302 на список студентів | `RedirectView` |
| `/admin/` | адмінпанель: групи, студенти з оцінками | `django.contrib.admin` |
| `/accounts/login/`, `/accounts/logout/` | вхід і вихід (вихід лише POST) | `django.contrib.auth.urls` |
| `/api/students/`, `/api/grades/` | REST API (див. «Вхід, ролі і REST API») | `StudentViewSet`, `GradeViewSet` |

Усі сторінки успадковують `templates/base.html`. Стилі лежать у
`students/static/students/style.css`; рядки оцінок на картці мають колір за
шкалою ECTS (фільтр `grade_class`). Для розгортання статичні файли збирають у
`staticfiles/` (тека в `.gitignore`):

~~~bash
uv run --env-file .env python manage.py collectstatic --noinput
~~~

Кожна відповідь має заголовок `Server-Timing` (час обробки, `TimingMiddleware`
стоїть першим у `MIDDLEWARE`) і `Content-Security-Policy`. Якщо база даних порожня
або недоступна, сторінки повертають 503 «Сервіс тимчасово недоступний», а причина
потрапляє в журнал сервера.

### База даних і адмінпанель

Сторінки читають дані з SQLite (`db.sqlite3`, файл не комітять). Моделі `Group`,
`Student` і `Grade` описано в `students/models.py`; модуль `students/services.py`
перетворює записи бази на об'єкти ядра, тож рейтинг і шкала ECTS, як і раніше,
обчислюються в `student_portal`. Перший запуск:

~~~bash
uv run --env-file .env python manage.py migrate
uv run --env-file .env python manage.py load_group data/group.json
uv run --env-file .env python manage.py createsuperuser
~~~

`load_group` можна запускати повторно: він оновлює тих самих студентів і замінює їхні
оцінки, копій не з'являється. Адмінпанель відкривається на
http://127.0.0.1:8000/admin/: список студентів має пошук і фільтр за групою, на
сторінці студента внизу редагуються оцінки. Бали понад 100 відхиляє і форма, і сама
база даних (обмеження `grade_score_at_most_100`).

Після зміни моделей створіть і закомітьте міграцію, а потім застосуйте її:

~~~bash
uv run --env-file .env python manage.py makemigrations students
uv run --env-file .env python manage.py migrate
~~~

Без міграції CI не пройде: крок `makemigrations --check --dry-run` завершиться з
кодом 1.

### Вхід, ролі і REST API

Увесь сайт закрито входом (`LoginRequiredMiddleware`): без входу будь-яка сторінка
перенаправляє на `/accounts/login/?next=...`. Відкриті лише сторінка входу і REST API,
який має власну перевірку (див. нижче). Ролі - це групи користувачів з правами
моделей; їх створює команда, яку можна запускати повторно:

~~~bash
uv run --env-file .env python manage.py setup_roles
~~~

| Роль (група) | Права | Що може |
| --- | --- | --- |
| Викладачі | `view_student`, `view_grade`, `add_grade` | переглядати студентів, виставляти оцінки |
| Деканат | `view_student`, `add_student`, `change_student`, `delete_student` | створювати, змінювати і видаляти студентів |
| без ролі | - | лише переглядати сторінки |

Користувачів додають в адмінпанелі й призначають їм групу. Права перевіряються на
сервері (`permission_required`, `PermissionRequiredMixin`, права DRF): без права
сторінка відповідає 403, а посилання «Нова оцінка», «Новий студент» і «Змінити»
показуються лише тим, кому дія дозволена. Форми надсилаються методом POST з
`{% csrf_token %}`, після успішного збереження - перенаправлення з повідомленням.

REST API побудовано на Django REST Framework. Доступ - лише після входу (сесія
браузера або HTTP Basic), зміни - за правами моделі (`DjangoModelPermissions`),
списки - по 20 записів (`?page=`).

| Метод | Адреса | Дія | Потрібне право |
| --- | --- | --- | --- |
| GET | `/api/students/` | список студентів із середнім балом і оцінками | вхід |
| POST | `/api/students/` | новий студент | `add_student` |
| GET | `/api/students/<id>/` | один студент | вхід |
| PUT, PATCH | `/api/students/<id>/` | зміна студента | `change_student` |
| DELETE | `/api/students/<id>/` | видалення студента | `delete_student` |
| GET | `/api/grades/` | список оцінок | вхід |
| POST | `/api/grades/` | нова оцінка | `add_grade` |

Оцінки через API лише створюються і переглядаються: змінювати і видаляти їх
можна в адмінпанелі. Приклад запиту:

~~~bash
curl -s -u teacher:<пароль> http://127.0.0.1:8000/api/students/
~~~

## Тести

Модульні тести pytest лежать у теці `tests/`, спільні фікстури - у `tests/conftest.py`.

~~~bash
uv run --env-file .env pytest                 # усі тести, короткий звіт
uv run --env-file .env pytest -v              # кожен тест окремим рядком
uv run --env-file .env pytest -k journal      # лише тести, у назві яких є «journal»
~~~

Налаштування Django читають ключ із середовища, тому без `--env-file .env`
pytest-django завершиться з `KeyError: 'DJANGO_SECRET_KEY'` ще до збирання тестів.
Тести працюють із файлами лише у тимчасовій теці (`tmp_path`) і не змінюють `data/`.
Тести, яким потрібна база, використовують окрему тестову базу pytest-django
(фікстури `db`, `db_group`, `admin_client`) і не залежать від `db.sqlite3`.
Фікстура `client` входить від імені користувача без ролі, `anonymous` - клієнт без
входу, `role_user` створює користувача в ролі «Викладачі» або «Деканат».
Мережу (`urlopen`), затримки розсилки і `input()` підміняють дублери, тож тести
не звертаються до сервера і нічого не чекають.

## Покриття і CI

Покриття рахується з розгалуженнями; поріг - 90 % (`[tool.coverage]` у
`pyproject.toml`), нижче нього `pytest --cov` завершується помилкою.

~~~bash
uv run --env-file .env pytest --cov                    # звіт у терміналі
uv run --env-file .env pytest --cov --cov-report=html  # HTML-звіт у htmlcov/index.html
~~~

На кожен pull request і push у `main` GitHub Actions (`.github/workflows/ci.yml`)
запускає два завдання: `checks` (Ruff, mypy, `manage.py check` і
`makemigrations --check`) і `tests` (pytest з покриттям,
HTML-звіт зберігається як артефакт `coverage-html`). Правило гілки `main`
дозволяє злиття лише після зелених `checks` і `tests`.

## Перевірки

~~~bash
uv run --env-file .env pytest
uv run --env-file .env python manage.py check
uv run ruff check .
uv run ruff format --check .
uv run mypy src
~~~

## Планування

Задачі та їхній статус ведуться на дошці GitHub Projects.
