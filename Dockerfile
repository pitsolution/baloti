FROM archlinux
RUN useradd --home-dir /app --uid 1000 app && mkdir -p /app && chown -R app /app
WORKDIR /app
RUN pacman -Syu --noconfirm gettext python python-psycopg2 python-pip uwsgi uwsgi-plugin-python python nano gmp python-psutil gcc mailcap
RUN pip3 install --upgrade pip wheel
ENV PYTHONIOENCODING=UTF-8 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ENV PATH=/app/node_modules/.bin:/app/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
USER app
COPY requirements.txt /app
RUN pip3 install --user -Ur /app/requirements.txt
COPY . /app/
RUN ./manage.py collectstatic
RUN find public -type f | xargs gzip -f -k -9

EXPOSE 8000
CMD /usr/bin/bash -euxc "until djcli dbcheck; do sleep 1; done \
  && ./manage.py migrate --noinput \
  && uwsgi \
  --http-socket=0.0.0.0:8000 \
  --chdir=/app \
  --plugin=python \
  --module=electeez.wsgi:application \
  --http-keepalive \
  --harakiri=1024 \
  --max-requests=100 \
  --master \
  --workers=12 \
  --processes=6 \
  --chmod=666 \
  --log-5xx \
  --vacuum \
  --enable-threads \
  --post-buffering=8192 \
  --ignore-sigpipe \
  --ignore-write-errors \
  --disable-write-exception \
  --mime-file /etc/mime.types \
  --thunder-lock \
  --offload-threads '%k' \
  --route '^/static/.* addheader:Cache-Control: public, max-age=7776000' \
  --route '^/js|css|fonts|images|icons|favicon.png/.* addheader:Cache-Control: public, max-age=7776000' \
  --static-map /static=/app/public \
  --static-gzip-all"