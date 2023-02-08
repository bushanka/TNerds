from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel
from src.secret.api_info import API_ID, API_HASH
from src.summarizer.summary import summ_text

client = TelegramClient('user_account', API_ID, API_HASH)


async def add_channels_to_main(channel_id):
    await client.connect()
    await client.get_dialogs()
    try:
        entity_channel = await client.get_entity(PeerChannel(int(channel_id)))
        print(entity_channel)
        return True
    except ValueError:
        return False


async def get_message_from_channel(channel_id=-1001392903897):
    # TODO Что если он не найдет такой id канала? Если добавить try-except то асинхронность блокируется почему-то
    await client.connect()
    channel_entity = await client.get_entity(PeerChannel(channel_id))
    # TODO Добавить тут ссылку на суммаризированный текст.
    summarized = []
    posts = await client(GetHistoryRequest(
        peer=channel_entity,
        limit=15,
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0,
        hash=0))
    for p in posts.messages:
        text = p.message
        post_time = p.date
        link = 't.me/' + channel_entity.username + '/' + str(p.id)
        if len(text) != 0:
            summarized.append((link, post_time, await summ_text(text)))
    print(summarized)
    return posts
