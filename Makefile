.ONESHELL:

.PHONY: install data launch lang

install:
	sudo apt install autoconf
	sudo apt install libtool
	sudo apt install pip
	sudo apt install libsodium-dev
	sudo apt install libsecp256k1-dev
	sudo apt install libpq-dev
	sudo apt install libmpfr-dev
	sudo apt install libmpc-dev
	pip install wheel
	pip install -U 'Twisted[tls,http2]'
	pip install -r requirements.txt
	pip install pytezos

data:
	./manage.py makemigrations
	./manage.py migrate
	./manage.py loaddata data.json
	./manage.py loaddata electis/site_data.json
	./manage.py loaddata electis/lang_data.json

run_all: runserver tezos_sync tezos_write tezos_balance ipfs

run:
	make -j 5 run_all

runserver:
	./manage.py runserver

tezos_sync:
	while true; do ./manage.py djtezos_sync; sleep 60; done

tezos_write:
	while true; do ./manage.py djtezos_write; sleep 30; done

tezos_balance:
	while true; do ./manage.py djtezos_balance; sleep 30; done

ipfs:
	ipfs daemon

lang:
	./manage.py loaddata electis/lang_data.json
