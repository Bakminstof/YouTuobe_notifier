Генерация сертификатов
```shell
HOST=""

TSL_DIR="certs"

PRIVATE_KEY="$TSL_DIR/notif-bot-private.pem"
PUBLIC_KEY="$TSL_DIR/notif-bot-public.pem"

openssl genrsa -out "$PRIVATE_KEY" 4096
openssl req -new -x509 -nodes -days 3650 -key "$PRIVATE_KEY" -out "$PUBLIC_KEY" -subj "/CN=$HOST"
```

start
```shell
docker image build -t nginx_r_proxy ./nginx
docker image build -t yt_notif_bot ./

docker stack deploy --with-registry-auth -c ./docker-compose.yaml youtube-notif-bot
```
