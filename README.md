# ABOUT THE ELECTIS VOTING APP

Electeez (electis.app) is an open source semi-decentralized voting platform.

It is using [election guard](https://www.electionguard.vote/) for its voting engine and
the [Tezos blockchain](tezos.com) to store the results in the form of a smart contract
pointing to an IPFS link with all the details to re-run an encrypted tally.

Electeez can be used for low-stakes elections when the organizer hosting the server can be trusted.

Electis.app is built to be as easy to use as possible for anyone to participate or organize elections.
It also allows technical auditors to verify as many pieces of information as possible
(e.g re-running the tally etc...)

The elections are organized by a Guardian (Multi guardians on our roadmap)
A guardian is in charge of keeping the private encryption
key(s) of the elections used to encrypt the ballots.

 Individual Ballots are always encrypted and their tallying is done via an homomorphic encryption
(only the sum of the ballots is decrypted) At the end of the election all the encrypted ballots and
the technical paramters of the elections are shared under a zipped artifacts file.

This allow a voter for example to verify that his/her ballot is present and
also that its hash (sha1) is the same as the information shared at the end of their vote.

This project is developed by electis in partnership with Tezos via its foundation #MORE INFO you can find more information about electis and electeez on https://www.electis.io/about you can test an online
version of electeez on https://www.electis.app

### MORE INFO
you can find more information about electis and electeez on https://www.electis.io/about
you can test an online version of electeez on https://www.electis.app


##  INSTALLATION ON UBUNTU

This readme and scripts are desinged for an Ubunutu install on localhost please adapt if
you are using another distro.

#### UPDATE / UPGRADE SYSTEM
```sh
sudo apt update
sudo apt upgrade
```

#### INSTALL / ELECTEEZ (ELECTIS.APP)
```sh
git clone https://gitlab.com/electisNGO/electeez.git
cd electeez
```

#### INSTALL PYTHON (IDEALLY >=3.9)
```sh
sudo apt install python3.9-dev
sudo apt install python3.9-venv
python3.9 -m venv my_env
```

#### LAUNCH VENV
```sh
source ./my_env/bin/activate
python -V #SHOULD BE 3.9+
```

#### INSTALL / RUN POSTGRESQL
```sh
sudo apt-get install postgresql
sudo systemctl start postgresql
```

#### INITIALIZE POSTGRESQL
```sh
sudo passwd postgres
su - postgres
createdb electeez
createuser <your_user_id>
exit
```

#### INSTALL / RUN MEMCACHED
```sh
sudo apt install memcached
systemctl enable memcached
systemctl start memcached
```

#### INSTALL IPFS
##### Follow IPFS install procedure on https://docs.ipfs.io/install/command-line/#official-distributions
##### Once ipfs is installed:
`ipfs init` #relaunch if queue error

#### INSTALL LIBS / PYTHON MODULES
`make install`

#### INITIALIZE THE DB FOR ELECTEEZ
`make data`

#### LAUNCH DJANGO SERVER
`make runserver`

#### CREATE A USER 
Go to 127.0.0.1:8000 then Sign up with <your_user_email> and check the logs for the email link. (cf the optional steps bellow if you whish to locate the emails logs in files instead of the console). Once your account is activated and you logged in stop the server and follow the next steps 


#### HOW TO MAKE A USER ADMIN 
```sh
./manage.py shell_plus
```

```python
u = User.objects.get(email="<your_user_email>")
u.is_superuser = True
u.is_staff = True
u.is_active = True
u.save()
quit()
```

#### LAUNCH ELECTIS APP
`make run` #TO LAUNCH ALL NEEDED SERVERS 


####  ACTIVATE YOUR TEZOS BLOCKCHAIN(S)
##### Go to the blockchain admin panel
127.0.0.1:8000/admin/djtezos/blockchain/
##### you will see a list of pre configured Tezos blockchains set as active, you can deactivate the one you don't need and then click save. 

#### ADD NEW TEZOS BLOKCHAIN(S) 
##### For example an Edo2net blockchain 
Click on Add a blockchain <br>
Name: Testnet Edonet <br>
EndPoint: https://rpc.tzkt.io/edo2net/ <br>
Explorer: https://edo2net.tzkt.io/{}/storage #{} is later replaced by the contract @ <br>
Provider Class: Tezos <br>
Confirmation Blocks: 2 <br>
Hit Save <br>

##### Special case, add a fake blockchain for local test 
Click on Add a blockchain <br>
Name: Fake <br>
EndPoint: 127.0.0.1:1337 (you can put any adress here) <br>
Explorer: <br>
Provider Class: Test <br>
Confirmation Blocks: 0 <br>
Hit Save <br>

##### When done you will see the list of active blockchain(s) under localhost:8000/en/tezos/'ELECTION_ID'/create/ URL 
##### Notice that a wallet address is created every time you add a new blockchain, you need to send the needed fund to the corresponding blockchain you are planning to use for your elections before launching one. We recommend at least 2XTZ. You can use the faucet bot on telegram to feed your Testnet wallets `https://t.me/tezos_faucet_bot`


#### (OPTIONAL) CHANGE EMAIL LOGS LOCATION 
When you signup, or do any action supposed to send an email, they will be
written in the console which you made `make run` in by default and which can be busy. 
If you want to get emails written in a file you must change the email backend
to `filebased` by changing the lines
`electeez_common/settings.py:`
```python
245     EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
246     # EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
247     # EMAIL_FILE_PATH = '/tmp/app-messages' # change this to a proper location
```
to:
```python
245     # EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
246     EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
247     EMAIL_FILE_PATH = '/tmp/app-messages' # change this to a proper location
```
And choose the location you want for `EMAIL_FILE_PATH` be sure to mkdir the path before launching it (e.g. : mkdir /tmp/app-messages)

