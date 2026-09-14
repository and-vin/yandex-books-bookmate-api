# Bookmate / Яндекс Книги — неофициальная карта API

Официального API и документации у сервиса нет. Карта восстановлена из трафика мобильного и веб-клиентов.

REST-факты (пути, коды ответа, поля моделей) формализованы в [`openapi.yaml`](./openapi.yaml), проверенном `openapi-spec-validator`. Статус проверки каждого пути — поля `x-verified`/`x-verified-date` там же. Этот markdown-файл — только для того, что в OpenAPI не выражается: хосты, авторизация, GraphQL, подводные камни формы данных, список непокрытых операций. Таблицы в §3 — короткий указатель путей, детали полей смотри в YAML.

Эндпоинты извлечения и расшифровки контента книг (`content/v4`, `metadata/v4`, `playlists.json`, comicbook `metadata.json`) не формализованы в OpenAPI — см. `x-content-extraction-excluded` в самой спеке.

## Оглавление

- [1. Хосты](#1-хосты)
- [2. Авторизация](#2-авторизация)
- [3. REST-эндпоинты](#3-rest-эндпоинты)
  - [3.1 Профиль и служебное (нужен токен)](#31-профиль-и-служебное-нужен-токен)
  - [3.2 Пользователи (публичные данные, токен не обязателен)](#32-пользователи-публичные-данные-токен-не-обязателен)
  - [3.3 Книги, аудиокниги, комиксы, серии](#33-книги-аудиокниги-комиксы-серии)
    - [3.3.1 Поиск (REST, без токена)](#331-поиск-rest-без-токена)
  - [3.4 Личная библиотека](#34-личная-библиотека)
    - [3.4.1 Свои цитаты, рецензии, уведомления](#341-свои-цитаты-рецензии-уведомления)
  - [3.5 Полки](#35-полки)
  - [3.6 Достижения, рецензии, каталог](#36-достижения-рецензии-каталог)
  - [3.7 Поля моделей вне OpenAPI](#37-поля-моделей-вне-openapi)
- [4. GraphQL](#4-graphql)
  - [4.1 GraphQL-шлюз веб-фронта (books.yandex.ru) — подписка на автора](#41-graphql-шлюз-веб-фронта-booksyandexru--подписка-на-автора)
- [5. Подводные камни](#5-подводные-камни)
- [6. Не покрыто / не существует](#6-не-покрыто--не-существует)
- [7. Источники](#7-источники)

---

## 1. Хосты

| База | Что это |
|---|---|
| `https://api.bookmate.yandex.net/api/v5` | REST мобильного приложения Яндекс Книги (RU) |
| `https://api.bookmate.ru/api/v5` | Тот же бэкенд, что `api.bookmate.yandex.net/api/v5` |
| `https://api-gateway.bookmate.yandex.net/graphql` | GraphQL-шлюз мобильного клиента (поиск, подписки, статистика) |
| `https://reader.bookmate.com/p/api/v5` | Тот же REST, веб-ридер международного Bookmate |
| `https://bookmate.com/p/api/v5` | REST через основной домен (cookie-авторизация) |
| `https://books.yandex.ru` | Веб-фронт Яндекс Книг, ссылки `/books/{uuid}`; отвечает напрямую (без редиректа на `reader.bookmate.com`) на `/reader/p/api/v5/metadata_secret`, `/p/api/v5/books/{uuid}/metadata/v4`, `/p/a/4/d/{document_uuid}/contents/OEBPS/{href}` — с cookie `Session_id`, без OAuth-токена |
| `https://books.yandex.ru/node-api/p-graphql/` | GraphQL-прокси веб-фронта (Next.js BFF, same-origin), отдельный от мобильного шлюза, свой вайтлист операций |

`/api/v5/...`, `/p/api/v5/...`, `/p/a/4/...` — один бэкенд за разными префиксами в пределах одного сервиса.

**С 24.02.2022 международный Bookmate и Яндекс Книги — разные бэкенды.** Следствия:
- аккаунт, подписка, библиотека не переносятся между сторонами;
- авторизация разная: у Bookmate — `BMS`-cookie `bookmate.com`, у Яндекс Книг — OAuth-токен Яндекса или cookie `yandex.ru` (§2);
- §3.3 «Файлы содержимого EPUB» составлен по клиентам международного Bookmate и не проверен против `api.bookmate.ru` напрямую;
- эта карта API сфокусирована на `api.bookmate.ru`/`api.bookmate.yandex.net` (Яндекс Книги); факты по международному Bookmate (`bookmate.com`) собраны частично, по независимым клиентам — см. §7 «Источники».

CDN статики (без авторизации): `https://api.bookmate.ru/assets/books-covers/{...}` — обложки; `https://api.bookmate.ru/pipeline/authors/{...}` — аватары авторов.

`https://audio.bookmate.ru` — вероятный CDN аудиотреков, точный путь не подтверждён.

---

## 2. Авторизация

**Вариант A — OAuth-токен (мобильный путь):**

```
https://oauth.yandex.ru/authorize?response_type=token&client_id=4483e97bab6e486a9822973109a14d05
```

Токен (`y0_AgAAAA...`) — из фрагмента редиректа на `yx4483e97bab6e486a9822973109a14d05.oauth.yandex.ru`, идёт в заголовке:

```
Auth-Token: y0_AgAAAA...
```

**Вариант B — cookie-сессия (веб):** `Session_id`, `sessionid2`, `yandex_login`, `yandexuid` для `https://yandex.ru`, запросы с `credentials: include`. Логин: `https://passport.yandex.ru/auth?origin=bookmate&retpath=...`.

**Заголовки клиента:**

```
App-Language: ru
App-Locale: ru
App-Platform: android
Device-Os: Android
Bookmate-Version: 20200305
User-Agent: okhttp/4.12.0
Accept-Encoding: gzip
Content-Type: application/json
```

GraphQL добавляет: `Accept: multipart/mixed; deferSpec=20220824, application/json`.

Опциональные заголовки старого Android-клиента: `app-user-agent`, `mcc`, `mnc`, `imei`, `subscription-country`, `device-idfa`, `onyx-preinstall`.

---

## 3. REST-эндпоинты

`{BASE} = https://api.bookmate.yandex.net/api/v5`.

### 3.1 Профиль и служебное (нужен токен)

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/profile` | Профиль текущего пользователя (ключ `user`) |
| GET | `/profile/counters` | Счётчики сообщений и уведомлений |
| GET | `/profile/notifications/status` | Статус уведомлений (`has_unread_notifications`) |
| GET | `/profile/access_levels` | Уровни доступа к контенту (подписка) |
| GET | `/profile/privacy_settings` | Настройки приватности |
| GET | `/profile/sync_state` | Состояние синхронизации |
| GET | `/context` | Контекст приложения |
| GET | `/metadata_secret` | Защищённые метаданные профиля (`secret`) |
| GET | `/a/4/user.json` | Полный JSON пользователя |
| GET | `/a/4/push_notification_settings/restrictions` | Ограничения push |
| GET | `/features?names[]=X&names[]=Y` | Флаги фич (имена — в OpenAPI, `getFeatures`) |

`/profile/reading_achievements` → `410 Gone` (отключено на сервере). `/profile/series/following` (без `{id}`) → `404`.

### 3.2 Пользователи (публичные данные, токен не обязателен)

`{id}` — числовой ID, UUID или псевдоним профиля. Поле ответа `login` — публичный псевдоним профиля Яндекс Книг, не логин Яндекс-аккаунта.

| Метод | Путь | Ответ |
|---|---|---|
| GET | `/users/{id}` | `user` |
| GET | `/users/{id}/books` | `books` |
| GET | `/users/{id}/audiobooks` | `audiobooks` |
| GET | `/users/{id}/comicbooks` | `comicbooks` |
| GET | `/users/{id}/bookshelves` | `bookshelves` |
| GET | `/users/{id}/followings` | `users` |
| GET | `/users/{id}/impressions` | `impressions` |
| GET | `/users/{id}/quotes?page=N&per_page=M` | `quotes` (только публичные), `per_page` работает минимум до 200 |
| GET | `/users/{id}/library_cards?page=N&per_page=M` | `500`, HTML вместо JSON — не работает. Не путать с `/profile/library_cards` (рабочий) |
| GET | `/users/{id}/reading_achievements` | `reading_achievements` |
| GET | `/users/{id}/series/following?page=N&per_page=M` | `series` |
| GET | `/profile/series/following?page=N&per_page=M` | `404`, см. OpenAPI `getMySeriesFollowing` |

### 3.3 Книги, аудиокниги, комиксы, серии

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/books/{uuid}` | Карточка книги (ключ `book`) |
| GET | `/books/{uuid}/impressions` | Рецензии на книгу |
| GET | `/books/{uuid}/content/v4` | Контент книги — EPUB (редирект на файл) |
| GET | `/books/{uuid}/metadata/v4` | Зашифрованные метаданные EPUB (container.xml, opf, ncx, `document_uuid`) |
| GET | `/books/{uuid}/episodes` | Эпизоды сериала (тип `serial`); на обычной книге `{"episodes": []}` |
| GET | `/audiobooks/{uuid}` | Карточка аудиокниги |
| GET | `/audiobooks/{uuid}/playlists.json` | Плейлист треков (`tracks[].offline[bitrate].url`) |
| GET | `/comicbooks/{uuid}` | Карточка комикса |
| GET | `/comicbooks/{uuid}/metadata.json` | Метаданные комикса, `uris.zip` → CBR-архив |
| GET | `/comicbooks/{uuid}/impressions` | Рецензии на комикс |
| GET | `/series/{uuid}` | Карточка серии |
| GET | `/series/{uuid}/parts` | Части серии (`parts[].resource.uuid`) |

Поля ответа `/users/{id}/books` — схема `Book` в OpenAPI.

### 3.3.1 Поиск (REST, без токена)

`{BASE} = https://api.bookmate.ru/api/v5`.

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/<resource>/search?query=…&page=…&per_page=…` | Поиск по типу: `books`, `audiobooks`, `comicbooks`, `series`, `authors`. Ответ: `{"objects": [...], "meta": {"total": {"value": N}, "page", "per_page", "query"}}` |
| GET | `/search?query=…` | Поиск по всем секциям (`books`, `audiobooks`, `comicbooks`, `series`, `authors`, `bookshelves`, `users`), ключ `search` |
| GET | `/authors/{uuid}` | Карточка автора |
| GET | `/authors/{uuid}/books?role=author` | Книги автора в роли `author`/`translator`/`narrator`/`illustrator`/`publisher` — `role` обязателен, без него `422` |

Формальные параметры (`query`, не `q`; лимит `per_page`, максимум 50) — в OpenAPI, `searchResource`. Практика применения:

- поиск нечёткий (по `Дюна` придут «Долина Дюн», «На дюнах») — сравнивать нормализованные названия и токены автора на своей стороне;
- не добавлять автора в строку запроса: токены объединяются по И, автор только сужает выдачу и теряет издания с другим написанием. Искать по названию, фильтровать по автору локально;
- пагинация отдаёт все результаты на первой странице, если их меньше `per_page`; вторая страница в этом случае пустая;
- поиск, `/users/{id}/books`, `/books/{uuid}` работают анонимно, без `Auth-Token` и cookie;
- рабочие заголовки без токена: `User-Agent: okhttp/4.12.0`, `Accept-Encoding: identity` (не `gzip`).

**Файлы содержимого EPUB (веб-ридер):**
```
GET https://reader.bookmate.com/p/a/4/d/{document_uuid}/contents/OEBPS/{href}
GET https://books.yandex.ru/p/a/4/d/{document_uuid}/contents/OEBPS/{href}
```
Второй путь работает и на `books.yandex.ru`, не только на `reader.bookmate.com`, через cookie-сессию (`Session_id`), без Auth-Token. `{href}` — из `content.opf`, `document_uuid` — из ответа `metadata/v4` (тот же путь на `books.yandex.ru`: `GET https://books.yandex.ru/p/api/v5/books/{uuid}/metadata/v4`; секрет расшифровки — `GET https://books.yandex.ru/reader/p/api/v5/metadata_secret?lang=ru`).

Аудио: URL трека — `.m3u8`; замена расширения на `.m4a` даёт прямой файл.

### 3.4 Личная библиотека

| Метод | Путь | Тело / параметры |
|---|---|---|
| GET | `/profile/library_cards?limit=50&offset=0` | `offset` и `limit` выше ~20 не влияют на ответ — всегда возвращаются те же ~20 самых свежих карточек. Не использовать для проверки «уже ли книга в библиотеке» — надёжнее ответ `POST /profile/library_cards` |
| GET | `/profile/books` | Книги профиля |
| POST | `/profile/library_cards` | `{"book_uuid": "..."}` → `200 {library_card}` — добавляет книгу из каталога в личную библиотеку. Если книга уже в библиотеке → `422 {"errors": "Эта книга уже есть в вашей библиотеке"}` (не `409`) — надёжный сигнал «уже отслеживается» |
| PUT | `/profile/library_cards/{uuid}` | `{"lc":{"uuid":"...","progress":100,"state":"finished","finished_at":<unix>}}` → `200 {library_card}` — помечает книгу прочитанной, значение реально сохраняется на сервере. `started_at`/`finished_at` через этот путь read-only: сервер отвечает `200`, но значения не переписываются — проставляются им самим при первой простановке `state` |
| DELETE | `/profile/library_cards/{uuid}` | 204 No Content |
| POST | `/profile/upload_books` | `multipart/form-data`: `public`, `files[]` (`.epub`/`.fb2`) → `204`, книга появляется в `GET /profile/library_cards` с `state="pending"`. См. `uploadBook` в OpenAPI — рейт-лимит, дедуп, требуемые заголовки |

Полный набор полей `library_card`: `accessed_at`, `changes_count`, `chapter_uuid`, `cfi`, `finished_at`, `fragment`, `progress`, `public`, `size_approx`, `started_at`, `state`, `sync_counter`, `title`, `uuid`, `last_read_excerpt`, `is_uploaded`, `document_uuid`, `is_in_child_library`, `book`. Подтверждённые значения `state`: `reading`, `pending` (только что загруженная через `upload_books` книга), `finished`. Схема `LibraryCard` — в OpenAPI.

### 3.4.1 Свои цитаты, рецензии, уведомления

| Метод | Путь | Ответ |
|---|---|---|
| GET | `/profile/quotes?page=N&per_page=M` | `{"quotes": [...]}` — свои цитаты. `include_private=true`/`visibility=all` не дают приватных цитат через REST |
| GET | `/profile/impressions?page=N&per_page=M` | `{"impressions": [...]}` — свои рецензии |
| GET | `/profile/notifications?page=N&per_page=M` | `{"notifications": [...]}` — лента (не только статус, как `/profile/notifications/status`) |

Схемы `Impression` и `Notification` — в OpenAPI.

### 3.5 Полки

| Метод | Путь | Примечание |
|---|---|---|
| GET | `/profile/bookshelves?page=1&per_page=20` | Мои полки |
| POST | `/bookshelves` | `multipart/form-data`: `bookshelf[title]`, `bookshelf[annotation]`, `bookshelf[cover]`, `bookshelf[state]=published` |
| GET | `/bookshelves/{uuid}` | Карточка полки |
| PUT | `/bookshelves/{uuid}` | Редактирование |
| DELETE | `/bookshelves/{uuid}` | Удаление |
| GET | `/bookshelves/{uuid}/books` | Книги на полке |
| GET | `/bookshelves/{uuid}/posts` | Посты полки (пагинация `page`, `per_page`) |
| POST | `/bookshelves/{uuid}/posts` | Добавить книгу на полку |
| DELETE | `/bookshelves/{uuid}/posts/{post_uuid}` | Убрать с полки |

### 3.6 Достижения, рецензии, каталог

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/profile/reading_achievements` | `410 Gone` — отключено на сервере |
| GET | `/profile/reading_achievements/{year}` | Тот же ресурс |
| GET | `/a/4/d/impressions/emotions` | Справочник эмоций для рецензий |
| GET | `/popular_searches/{lang}?page=1` | Популярные запросы (`ru`, `en`, …) |
| GET | `/catalog` | `{"topics": [...]}` — дерево тем/жанров, токен не обязателен |

`/catalog/topics`, `/topics/popular`, `/main`, `/main_screen`, `/widgets`, `/collections`, `/genres`, `/topics`, `/profile/followings`, `/profile/followers`, `/profile/subscriptions`, `/profile/devices`, `/profile/payments`, `/profile/subscription` → `404`.

### 3.7 Поля моделей вне OpenAPI

Сущности без отдельной схемы в OpenAPI:

- **`Audiobook(Book)`**: `document_uuid`, `can_be_listened`, `duration` (секунды), `listeners_count`, `narrators`.
- **`Comicbook(Audiobook)`**: `comic_card`, `pages_count`.
- **`Series`**: `uuid`, `title`/`name`, `description`, `books_count`, `followers_count`, `cover`, `authors`.

---

## 4. GraphQL

`POST https://api-gateway.bookmate.yandex.net/graphql`

Тело: `{"operationName": ..., "variables": {...}, "query": "..."}`.

Шлюз работает по вайтлисту персистентных запросов (хэш, не текст) — интроспекция и произвольный текст запроса отвечают `Whitelist: query not found`, даже для реконструированного текста существующей операции.

| Операция | Переменные | Что отдаёт |
|---|---|---|
| `Search` | `query: SearchParamsInput!` → `{cursor, noMisspell, query, types}` | `TextBook`, `AudioBook`, `ComicBook`, `TextSerial`, `Bookshelf`, `Person`, `Publisher`, `Series`, `Topic`, `User`; плюс `cursor`, `rankedFilter`, `misspell` |
| `ProfileSubscriptions` | `subscriptionParams: SubscriptionParamsInput!` → `{cursor, perPage, subscriptionFilterSource: ["SUBSCRIPTION_FILTER_SOURCE_PERSON"]}` | Подписки на авторов |
| `Statistics` | `requestTime: DateTime!` (ISO-8601) | `user.loyalty.statistics`: `daysPerMonth`, `streak`, `streakRecord`, `todayTime` |

Типы схемы: `Cover { url ratio backgroundColorHex }`, `Person { avatar name uuid worksCount roles }`, `Book { annotation name cover uuid authors ageRestriction editorAnnotation publisher translators topics subscriptionLevels tags }`, `Progress { finished inLibrary progress isPublic }`, `AudioBook { narrators listenersCount }`, `TextBook { readersCount }`, `TextSerial { episodes { total } }`, `Bookshelf { name uuid user posts { total } followersCount description }`, `Series { authors cover name uuid items { followersCount total } }`, `Topic { name slug totalBook uuid parent }`.

### 4.1 GraphQL-шлюз веб-фронта (books.yandex.ru) — подписка на автора

`POST https://books.yandex.ru/node-api/p-graphql/` — отдельный хост и вайтлист от мобильного шлюза выше.

**Мутация `SubscribeToPerson`** — подписка на автора:

```json
{
  "operationName": "SubscribeToPerson",
  "variables": {"uuid": "<author uuid>", "source": "SOURCE_PERSON"},
  "query": "mutation SubscribeToPerson($uuid: ID!, $source: Source!) {\n  subscribe(uuid: $uuid, source: $source) {\n    muted\n    __typename\n  }\n}"
}
```

→ `200 {"data": {"subscribe": {"muted": false, "__typename": "Subscription"}}}`.

Авторизация — заголовок `Auth-Token` (тот же токен, что и REST на `api.bookmate.ru`), не cookie веб-сессии. Без него — `200` с ошибкой в теле: `{"errors": [{"message": "Invalid Header value for Auth-Token or X-Ya-User-Ticket", "extensions": {"type": "INVALID_HEADER"}}]}`. Другие варианты заголовка (`Authorization: OAuth`/`Bearer`, `Cookie: Session_id=`) не работают — только точное имя `Auth-Token`.

Отписка и чтение списка подписок с этого хоста не проверялись — для чтения подписок используется `ProfileSubscriptions` на мобильном шлюзе (см. выше).

---

## 5. Подводные камни

- **Шифрование метаданных.** `books/{uuid}/metadata/v4` возвращает поля-массивы байт, AES-CBC. Ключ (`secret`) — base64 из `client_params` HTML-страницы `https://reader.bookmate.com/{bookid}`; IV — первые 16 байт, паддинг PKCS-подобный.
- **Приватные цитаты недоступны через REST.** Нужна фронтовая GraphQL/BFF-операция.
- **429 Too Many Requests** при скачивании глав — нужен ретрай с backoff.
- **Коды ошибок:** 400 → BadRequest, 401/403 → Unauthorized, 404 → NotFound; сообщение в теле по ключам `message` / `error` / `errors[0].message`. Форма ответа `Error` — вложенная: `{"error": {"code", "message"}}`.
- **Именование полей смешанное:** camelCase в GraphQL, snake_case и kebab-case в REST.
- **`in_library` / `in_wishlist` в анонимных ответах всегда пустые/`false`** (`/search`, `/<resource>/search`, `/users/{id}/books`) — анонимный запрос не знает пользователя. Чтобы получить реальный статус своей библиотеки, нужны авторизованные эндпоинты (`/profile/library_cards`, `/profile/books`, §3.4), а не анонимное чтение.
- **Расхождения форм с независимыми клиентами** (`stepan163s/yandex-book-api`): `LibraryCard` — реальные поля `reading_progress`/`added_at`/`updated_at` отсутствуют; `impressions[]` — реальные поля `emotions`/`creator`, не `emotion`/`user`, без `updated_at`; `User` из поиска — уже, чем `/users/{id}` (без `uuid`, с `cards_count`/`following`); `Topic.icon` — base64 PNG, не URL; `Topic.background` — объект `{large}`, не строка; `SearchMeta` дополнен `relation`, `matches_user_lang`, `url`; `meta.total` в секции `series` из `/search` — голое число.
- Приватный API без гарантий стабильности: версии, пути, вайтлист могут измениться без предупреждения. Скачивание платного контента нарушает пользовательское соглашение.

---

## 6. Не покрыто / не существует

- Создание и удаление цитат и рецензий — чтение работает (`/profile/quotes`, `/profile/impressions`, §3.4.1), путь записи не найден.
- Подписка/отписка на авторов через REST не существует (`/profile/subscriptions`, `/profile/followings`, `/profile/followers` → `404` на GET и на POST/PUT); GraphQL-мутация на мобильном шлюзе (`api-gateway.bookmate.yandex.net/graphql`) тоже не проходит вайтлист. Рабочий путь — `SubscribeToPerson` на BFF веб-фронта, §4.1.
- Подборки и рекомендации главной страницы (`/main`, `/main_screen`, `/widgets`, `/collections`, `/recommendations`) не существуют — есть только каталог тем (§3.6).
- Платёжные и подписочные ручки не существуют (`/profile/payments`, `/profile/subscription`); `/profile/access_levels` (§3.1) показывает только текущий уровень доступа.
- Websocket не задокументирован (заголовок `bookmate-websocket-version` встречается в трафике клиента, назначение не изучено).
- GraphQL мобильного шлюза (§4) не расширяется дальше трёх задокументированных операций: вайтлист принимает только персистентные хэши, произвольный текст запроса отклоняется.

Дальнейший сбор фактов — mitmproxy на Android-клиенте либо DevTools на `books.yandex.ru`, выгрузка в Swagger через `mitmproxy2swagger`. Угадывание путей по конвенциям именования работает для GET чтения собственных данных, не годится для мутирующих операций.

---

## 7. Источники

Независимые клиенты, покрывающие российскую сторону (`api.bookmate.yandex.net`/`api.bookmate.ru`) и международный Bookmate (`bookmate.com`):

| Репозиторий | Чем полезен |
|---|---|
| `stepan163s/yandex-book-api` | Самый полный клиент: REST v5 + GraphQL, ~40 методов |
| `zhenya-yadlovskij/yandex-book-api-ts` | TS-порт `stepan163s/yandex-book-api` |
| `kettle017/RU_Bookmate_downloader` | Контентные эндпоинты: EPUB, playlists, comics, series |
| `alunyaka/obsidian-yandex-books-plugin` | Цитаты, пагинация |
| `Sirozha1337/bookmate_downloader_extension` | Веб-ридер, аудиокниги, cookie-авторизация |
| `ilyakharlamov/bookmate_downloader` | Расшифровка `metadata/v4`, сборка EPUB |
| `gusenov/bookmate-sh` | PUT приватности карточек, cookie-запросы к `bookmate.com` |
| `vonoelv/bookmate-test-project` | API-тесты: полки, посты, library_cards, форматы тел запросов |
| `dvorobiev/yandex-books-downloader` | Хост CDN аудиотреков `audio.bookmate.ru` |
| `alex123012/yandex_books_downloader` | Контентные пути `metadata_secret`/`metadata/v4`/`contents/OEBPS/{href}` (§3.3) работают напрямую на `books.yandex.ru`, не только на `reader.bookmate.com` |
