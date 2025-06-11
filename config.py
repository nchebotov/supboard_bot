import os
import json
from pathlib import Path
from dotenv import load_dotenv


environment = os.environ.get('ENV')
env_path = Path('.') / '.env'

load_dotenv(dotenv_path=env_path)


RENTAL_RATE = float(os.getenv('RENTAL_RATE', 500.00))
BOT_TOKEN = os.getenv('BOT_TOKEN', None)
ADMINS = [
    int(x)
    for x in os.getenv('ADMINS', None).split(',')
]

# Настройки Google Sheets
GS_CREDENTIALS = json.loads(os.getenv('CREDENTIALS'))
GS_SPREADSHEET_ID = os.getenv('GS_SPREADSHEET_ID')        # ID существующей таблицы
GS_WORKSHEET_NAME = 'Лист1'            # имя листа (или можно оставить 'Sheet1')
GS_URL_TEMPLATE = 'https://docs.google.com/spreadsheets/d/{sheet_id}/view?usp=sharing'

# SupBoards
SAPBOARDS=json.loads(os.getenv('SUPBOARDS'))
