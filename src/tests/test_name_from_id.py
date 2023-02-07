import requests
from src.secret.api_info import BOT_TOKEN


def get_channel_name(channel_id, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/getChat?chat_id={channel_id}"
    response = requests.get(url)
    if response.status_code == 200:
        chat = response.json()["result"]
        return chat["title"]
    else:
        print(response.text)
    return None


print(get_channel_name(-1001392903897, BOT_TOKEN))
