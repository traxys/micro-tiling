#!/bin/bash
gunicorn --workers=1 wat:app
