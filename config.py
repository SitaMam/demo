import os

#Bot token @Botfather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

#Your API ID from my.telegram.org
API_ID = int(os.environ.get("API_ID", "20166660"))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "ac8d8536e2869da1e2388cea87d3e5f7")

#Database 
DB_URI = os.environ.get("DB_URI", "mongodb+srv://sarinaviolet:Bycvt1Zrm91wDAwQ@cluster0.z5hz1.mongodb.net/?retryWrites=true&w=majority")