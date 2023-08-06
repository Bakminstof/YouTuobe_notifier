# YouTube notifier bot
## Телеграм бот для отправки уведомлений с YouTube
### Запуск сервиса

Сервис можно запустить в двух режимах: long polling(бот сам периодически отправляет запросы в Telegram) 
и webhook(Telegram отправляет запросы боту через вебхук).

Для начала нужно установить Loki для логирования в Dokcer контейнерах. 

Команда для установки Loki драйвера:
`docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions`

- ### Long polling
    Для запуска сервиса сконфигурировать файлы:
  - Bot: `youtube_notifier_bot/bot/environment/` В `dev.env` или `prod.env` 
  указать `BOT_TOKEN`, `DB_PASS`, `WEBHOOK=False`. По желанию в выбранном .env файле можно
  добавить в список `ADMINS` telegram_id администраторов бота. 
    - PostgresSQL: `postgres/` 
      - В `pg.env` указать `POSTGRES_USER` и `POSTGRES_PASSWORD` 
      они будут использованы тут -> `init.sql`.
      - В `init.sql` в функции dblink_exec указать `user` и `password` такие же, 
      как `POSTGRES_USER` и `POSTGRES_PASSWORD` в `pg.env`. Заменить `CHANGE_MEE!!` на пароль 
      от базы данных, который указан в `DB_PASS` в `dev.env` или в `prod.env`  

  Далее необходимо собрать и поднять все контейнеры:
  `docker-compose up --build -d postgres youtube_notifier_bot grafana loki`

- ### Webhook
    Также нужно сконфигурировать файлы:
  - Bot: `youtube_notifier_bot/bot/environment/` В `dev.env` или `prod.env` 
  указать `BOT_TOKEN`, `DB_PASS`, `WEBHOOK=True`, также указать хост для вебхука 
  `WEBHOOK_HOST`.
    - PostgresSQL: Всё также как и в Long polling режиме.
    - Nginx: `nginx/` (`nginx.conf` - в разделе 
    `location` `bot_token` заменить на токен бота)
    - TSL: Запустить `gen_tsl.sh` с указанием хоста вебхука.(Пример `bash gen_tsl.sh 124.55.78.194`)
  
  Собрать и поднять все контейнеры: `docker-compose up --build -d`

#### Логирование
Для логирования в контейнерах используется Loki, 
также логи записываются в файлы в папке `youtube_notifier_bot/bot/logging_data/logs`.
Для визуализации логов используется Grafana. Она доступна по адресу: `http://localhost:3000/`. 
Для отображения логов в Grafana нужно в Data sources указать Loki и его URL `http://loki:3100/`


#### Бэкап базы:
Для настройки ежедневного бэкапа базы необходимо в `postgres/backup_scripts/` в `do_backup.sh` 
указать данные для подключения к базе (`POSTGRES_HOST`, `POSTGRES_PORT`, `PGPASSWORD`, `POSTGRES_USER`),
запустить cron `crontab -e`и добавить туда следующую строку 
`3 0 * * * docker exec postgres_container bash /var/lib/postgresql/backup_scripts/do_backup.sh`.
Теперь будет производиться бэкап базы каждую ночь 3 часа.
