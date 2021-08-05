FROM archlinux:base-20210131.0.14634
RUN useradd --home-dir /app --uid 1000 app && mkdir -p /app/log && chown -R app /app
WORKDIR /app
RUN echo '[testing]' >> /etc/pacman.conf
RUN echo Include = /etc/pacman.d/mirrorlist >> /etc/pacman.conf
RUN pacman -Syu --noconfirm vim mailcap which gettext python python-pillow python-psycopg2 python-pip python-psutil git curl uwsgi uwsgi-plugin-python python make gcc cython pkg-config graphviz libsodium libsecp256k1 go-ipfs && rm -rf /var/cache/pacman/pkg
RUN pip3 install --upgrade pip wheel
ENV PYTHONIOENCODING=UTF-8 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ENV PATH=/app/node_modules/.bin:/app/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN mkdir -p /spooler/blockchain /spooler/email && chown -R app /spooler
COPY requirements.txt /app
RUN pip3 install -Ur /app/requirements.txt
COPY . /app/
RUN DEBUG= ./manage.py ryzom_bundle
RUN DEBUG= ./manage.py compilemessages
RUN chown -R app. /app/log
USER app

EXPOSE 8000
CMD /usr/bin/bash -euxc "until djcli dbcheck; do sleep 1; done \
  && ./manage.py compilescss \
  && ./manage.py collectstatic --noinput \
  && ./manage.py migrate --noinput \
  && ./manage.py loaddata ${DJANGO_APP}/site_data.json \
  && ./manage.py loaddata ${DJANGO_APP}/lang_data.json \
  && find public -type f | xargs gzip -f -k -9 \
  && uwsgi \
  --http-socket=0.0.0.0:8000 \
  --chdir=/app \
  --plugin=python \
  --spooler=/spooler/blockchain \
  --spooler=/spooler/email \
  --spooler-processes=8 \
  --spooler-frequency=1 \
  --spooler-chdir=/app \
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
  --static-map /media=/app/media \
  --static-gzip-all"
