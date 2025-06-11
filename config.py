import os
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
GS_CREDENTIALS = {
  "type": os.getenv('TYPE'),
  "project_id": os.getenv('PROJECT_ID'),
  "private_key_id": os.getenv('PRIVATE_KEY_ID'),
  "private_key": os.getenv('PRIVATE_KEY'),
  "client_email": os.getenv('CLIENT_EMAIL'),
  "client_id": os.getenv('CLIENT_ID'),
  "auth_uri": os.getenv('AUTH_URI'),
  "token_uri": os.getenv('TOKEN_URI'),
  "auth_provider_x509_cert_url": os.getenv('AUTH_PROVIDER_X509_URL'),
  "client_x509_cert_url": os.getenv('CLIENT_X509_CERT_URL'),
  "universe_domain": os.getenv('UNIVERSE_DOMAIN')
}

GS_SPREADSHEET_ID = os.getenv('GS_SPREADSHEET_ID')        # ID существующей таблицы
GS_WORKSHEET_NAME = 'Лист1'            # имя листа (или можно оставить 'Sheet1')
GS_URL_TEMPLATE = 'https://docs.google.com/spreadsheets/d/{sheet_id}/view?usp=sharing'

# SupBoards
SAPBOARDS={
    str(key):value
    for key, value  in enumerate(os.getenv('SUPBOARDS', None).split(','), start=1)
}
