# CinemaCity Viber Bot
"SELECT value FROM config WHERE param=token",
                                         {'param': param}).fetchone()[0]
										 
import sqlite3
import sqlite3

con = sqlite3.connect("vbot.db")
cur = con.cursor()

res = cur.execute("SELECT * FROM config;")
res = cur.execute("SELECT * FROM cinemas;")
res = cur.execute("SELECT * FROM users;")
res.fetchall()

res = cur.execute("SELECT * FROM users WHERE;")
res.fetchall()
Ngrok needs account and auth key - use cmd not ps:
ngrok http 5000

make sure you use CMS and not PW for his command (and add /vbot endpoint at the end of ngrok's url):
curl -# -i -g -H "X-Viber-Auth-Token:<token>" -d @misc\viber.json -X POST https://chatapi.viber.com/pa/set_webhook -v

crontab -l
pkill gunicorn; cd $HOME/cinemacity/viber_bot; gunicorn3 --workers=1 vbot:app --daemon


VATICAN
to START:
cd ~/cinemacity/viber_bot
nohup python3 -m misc.vatican > misc/vatican.log 2>&1 &
disown

// alternative
python3 -m misc.vatican

CHECK_RUNNING:
ps aux | grep vatican

STOP:
pkill -f misc.vatican

@reboot sleep 90 && cd $HOME/cinemacity/viber_bot && nohup python3 -m misc.vatican > misc/vatican.log 2>&1 & disown