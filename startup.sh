#!/bin/bash
# Azure App Service startup script
# Run database migrations then start the bot
python -m alembic upgrade head
python app.py
