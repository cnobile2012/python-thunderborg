#!/usr/bin/env bash

TBORG_VE=$HOME/.virtualenvs/tborg3
TBORG_VE_BIN=$TBORG_VE/bin
TBORG_HOME=$HOME/src/python-thunderborg
PYTHON_PATH=$(find "$TBORG_VE/lib" -maxdepth 2 -type d -name "python3.*" \
                   -print -quit)
SITE_PACKAGES=$PYTHON_PATH/site-packages

if [ -d "$SITE_PACKAGES" ]; then
    #printf "Found site-packages at: %s\n" $SITE_PACKAGES
    export PYTHONPATH="$SITE_PACKAGES:$PYTHONPATH"
    $TBORG_VE_BIN/python $TBORG_HOME/tborg/examples/mborg_pygame.py \
                         --voltage-in=0 > /tmp/mborg_pygame_cron.log 2>&1
else
    printf "site-packages not found inside %s\n" $PYTHON_PATH
fi
