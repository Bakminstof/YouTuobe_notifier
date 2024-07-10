## Бот для рассылки уведомлений о выходе нового контента на YouTube.

[Бот](https://t.me/youtube_notifier_simple_bot/ "Бот уведомлений от YouTube") для отправки уведомлений о выходе новых видео или трансляций, 
который реализован на Aiogram 3.6. В роли базы данных выступает SQLite. Для настройки используется файл
с переменными окружения __.env.template__(./src/env). Для запуска необходимо вписать токен бота в __.env.template__
и в __nginx.conf__(./nginx/config) вместо BOT_TOKEN.

Управление режимом работы (long polling или webhook) осуществляется переменной окружения __APP.WEBHOOK.ACTIVE__.
Если она она __True__ - режим __webhook__, иначе - __long polling__.

В режиме __webhook__ нужны ключи шифрования для Телеграм сервера. 
```shell
HOST="HOST_HERE"  # Указать свой IP 

TSL_DIR="certs"

PRIVATE_KEY="$TSL_DIR/notif-bot-private.pem"
PUBLIC_KEY="$TSL_DIR/notif-bot-public.pem"

openssl genrsa -out "$PRIVATE_KEY" 4096
openssl req -new -x509 -nodes -days 3650 -key "$PRIVATE_KEY" -out "$PUBLIC_KEY" -subj "/CN=$HOST"
```
Также для обоих режимов необходим секретный ключ __APP.SECRET_TOKEN__. Он может состоять только из латинских букв
разного регистра и символа подчеркивания (a-zA-Z_). 
 

Далее остаётся только собрать и запустить docker-контейнеры:
```shell
docker image build -t nginx_r_proxy ./nginx
docker image build -t yt_notif_bot ./

docker stack deploy --with-registry-auth -c ./docker-compose.yaml youtube-notif-bot
```
