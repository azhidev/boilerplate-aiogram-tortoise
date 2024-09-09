import os, dotenv

dotenv.load_dotenv(os.path.join(".env"))

BOT_TOKEN=os.getenv("BOT_TOKEN")

TORTOISE_ORM = {
    "connections": {
        "default": os.getenv("SQL_ADDRESS")
    },
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": False,
    "timezone": "UTC"
}
