#!/usr/bin/env bash

HOME=/home/pi/
TBORG_VE=$HOME.virtualenvs/tborg3
TBORG_VE_BIN=$TBORG_VE/bin
TBORG_HOME=$HOME/src/python-thunderborg
export PYTHON_PATH=$TBORG_VE/lib/python3.5/site-packages/

$TBORG_VE_BIN/python $TBORG_HOME/tborg/examples/mborg_approxeng.py > /tmp/mborg_approxeng_cron.log 2>&1
