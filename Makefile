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

run: 
	./manage.py runserver

lang:
	./manage.py loaddata electis/lang_data.json 
