from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

# Remember to use your own values from my.telegram.org!
api_id = 23047997
api_hash = 'f8bb4aa514638133db7fe8a70f9f20eb'
client = TelegramClient('main_account', api_id, api_hash)


async def main():
    # Getting information about yourself
    # me = await client.get_me()

    # "me" is a user object. You can pretty-print
    # any Telegram object with the "stringify" method:
    # print(me.stringify())
    print('GOgoGO')
    d = await client.get_dialogs()
    unread_d = []

    for el in d:
        if el.unread_count != 0:
            unread_d.append(el)

    print(unread_d)
    #todo Тут сделано только для одного диалога, надо сделать если их много
    if len(unread_d) != 0:
        num_unread = unread_d[0].unread_count

        channel_entity = await client.get_entity(unread_d[0].entity)
        posts = await client(GetHistoryRequest(
            peer=channel_entity,
            limit=num_unread,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0))
        for messages in posts.messages:
            print('_____________________')
            print(messages.message)
            print('_____________________')

with client:
    client.loop.run_until_complete(main())
