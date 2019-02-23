#!/bin/sh

SERVICE_ROOT=$(dirname $BASH_SOURCE)
SERVICE_ROOT=$(realpath $SERVICE_ROOT)
cd $SERVICE_ROOT/gopher; python golfer.py & cd $SERVICE_ROOT/a_pi; flask run & cd $SERVICE_ROOT/Millllllll; python millllllll.py
