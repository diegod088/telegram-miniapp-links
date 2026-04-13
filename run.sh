#!/bin/bash
source venv/bin/activate
export PYTHONPATH=.

python app.py &
flask_pid=$!

python bot1.py &
bot1_pid=$!

python bot2.py &
bot2_pid=$!

trap "kill $flask_pid $bot1_pid $bot2_pid" SIGINT SIGTERM
wait
