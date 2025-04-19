import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_LINK_CONNECTION = os.getenv('DB_LINK_CONNECTION')
DEEPDEEK_KEY = os.getenv('DEEPDEEK_KEY')
