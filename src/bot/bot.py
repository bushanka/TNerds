import asyncio
from telethon import TelegramClient, events
from telethon import Button
from enum import Enum, auto
from src.database.sql_query import sql_query
from src.secret.api_info import API_ID, API_HASH, BOT_TOKEN
from src.bot.reply_texts import GREET_TEXT, ADD_CHANNELS_TEXT, ACTIVATE_TEST_ACCESS, NOT_SUBSCRIBER, IS_SUBSCRIBER, \
    CHANNEL_ADDED, ERROR_CHANNEL_ALREADY_EXISTS, ERROR_MESSAGE_NOT_FROM_PUBLIC
import datetime
from src.client.client import get_message_from_channel, add_channels_to_main
from src.summarizer.summary import summ_text


class State(Enum):
    """Finite State Machine."""
    WAIT_LIST_TG_CHANNELS = auto()


# The state in which different users are, {user_id: state}
conversation_state = {}

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


def markup_generator(user_id):
    """Генерация кнопок-ответов"""
    if sql_query("SELECT first_time_test_access "
                 "FROM users_data "
                 "WHERE userid = ?;",
                 params=(user_id,))[0][0] == 1:

        markup = [
            [
                Button.inline('Дайджест', b'digest'),
                Button.inline('Добавить каналы', b'add_channels'),
            ],
            [
                Button.inline('Удалить каналы', b'delete_channels'),
                Button.inline('Подписка', b'subscription'),
            ],
            [
                Button.inline('Получить тестовый доступ', b'test_access')
            ]
        ]
    else:
        markup = [
            [
                Button.inline('Дайджест', b'digest'),
                Button.inline('Добавить каналы', b'add_channels'),
            ],
            [
                Button.inline('Удалить каналы', b'delete_channels'),
                Button.inline('Подписка', b'subscription'),
            ]
        ]
    return markup


@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Функция обрабатывает /start - начальное сообщение. Происходит запись пользователя в базу данных"""
    sender = await event.get_sender()
    user_info = (sender.id, sender.username)

    data_main = sql_query("SELECT userid "
                          "FROM users_data "
                          "WHERE userid = ?;",
                          params=(user_info[0],))

    if len(data_main) == 0:
        sql_query("""INSERT INTO users_data(userid, username) 
                     VALUES(?,?);""",
                  params=user_info)

    markup = markup_generator(user_info[0])

    await event.respond(GREET_TEXT, buttons=markup)

    raise events.StopPropagation  # TODO разобраться что делает эта строка кода


@bot.on(events.CallbackQuery(data=b'add_channels'))
async def handler_digest(event):
    """Добавляет каналы в дайджест пользователя"""
    await event.respond(ADD_CHANNELS_TEXT, buttons=Button.inline('Назад', b'back_to_main'))
    conversation_state[event.sender_id] = State.WAIT_LIST_TG_CHANNELS


@bot.on(events.CallbackQuery(data=b'back_to_main'))
async def handler_digest(event):
    """Возврат в галвное меню при отмене добавления каналов."""
    sender = await event.get_sender()
    user_info = (sender.id, sender.username)

    markup = markup_generator(user_info[0])

    try:
        del conversation_state[event.sender_id]
    except KeyError:
        pass

    await event.respond(GREET_TEXT, buttons=markup)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(data=b'test_access'))
async def handler_digest(event):
    """Активирует тестовый доступ к боту."""
    sender = await event.get_sender()
    user_info = (sender.id, sender.username)

    sql_query(
        f"UPDATE users_data "
        f"SET first_time_test_access = ?, time_send_digest = ?, time_end_subscription = ?, is_subscriber = ? "
        f"WHERE userid = ?;",
        params=(0, '12:00',
                (datetime.datetime.now() + datetime.timedelta(days=3)).strftime("%d.%m.%Y"),
                1, user_info[0]))

    markup = markup_generator(user_info[0])

    await event.respond(ACTIVATE_TEST_ACCESS, buttons=markup)


@bot.on(events.CallbackQuery(data=b'subscription'))
async def handler_digest(event):
    """Проверяет подписку"""
    sender = await event.get_sender()
    user_info = (sender.id, sender.username)

    time_end_subscription, is_subscriber = sql_query(
        f"SELECT time_end_subscription, is_subscriber "
        f"FROM users_data "
        f"WHERE userid = ?;",
        params=(user_info[0],))[0]

    if not is_subscriber:
        await event.respond(NOT_SUBSCRIBER, buttons=[Button.inline('Оформить подписку', b'get_subscription'),
                                                     Button.inline('Назад', b'back_to_main')])
    else:
        await event.respond(IS_SUBSCRIBER + f'{time_end_subscription}',
                            buttons=[Button.inline('Продлить подписку', b'prolong_subscription'),
                                     Button.inline('Назад', b'back_to_main')])


@bot.on(events.CallbackQuery(data=b'digest'))
async def handler_digest(event):
    """Формирует дайджест и присылает его пользователю"""
    # TODO Добавить функцию суммаризатора ассинхронную (aiohttp?), вынести эту функци в отдельную, чтобы вызывать ее внутри кода
    # TODO Сделать рассылку по времени. Добавить ссылку на источник в суммаризированный текст - есть канал - есть инфа по нему - есть и ссылка
    sender = await event.get_sender()
    user_info = (sender.id, sender.username)

    channels = (sql_query('SELECT public FROM users_data WHERE userid = ?;', params=(user_info[0],))[0][0]).split(',')
    channels = [int(k) for k in channels[:len(channels) - 1:]]

    coros = [get_message_from_channel(ch) for ch in channels]

    digest = await asyncio.gather(*coros)

    await event.respond(str(digest[0].messages[0].message), buttons=Button.inline('Назад', b'back_to_main'))


@bot.on(events.NewMessage())
async def handler(event):
    """Добавляет тг паблики."""
    sender = await event.get_sender()
    user_info = (sender.id, sender.username)

    state = conversation_state.get(user_info[0])
    if state == State.WAIT_LIST_TG_CHANNELS:
        message = event.message
        # print(message)
        try:
            prev_public = sql_query(f"SELECT public "
                                    f"FROM users_data "
                                    f"WHERE userid = ?;", params=(user_info[0],))[0][0]
            new_public = str(message.fwd_from.from_id.channel_id)

            # TODO автоматически подписиваться на паблики как?

            # ПРОВЕРКА, ЕСТЬ ЛИ ПАБЛИК В ПОДПИСКАХ, ЕСЛИ НЕТ, ОТПРАВЛЯЕТ ПЕРЕСЛАННОЕ СООБЩЕНИЕ
            check_public = await add_channels_to_main(new_public)

            if not check_public:
                # ЕСЛИ НЕТУ, ТО НАДО ВРУЧНУЮ ПОДПИСЫВАТЬСЯ
                await bot.forward_messages(5706775497, message)

            if new_public not in prev_public:
                sql_query(f"UPDATE users_data "
                          f"SET public = ? "
                          f"WHERE userid = ?;", params=(prev_public + new_public + ', ', user_info[0]))
                await event.respond(CHANNEL_ADDED, buttons=Button.inline('Назад', b'back_to_main'))
            else:
                await event.respond(ERROR_CHANNEL_ALREADY_EXISTS, buttons=Button.inline('Назад', b'back_to_main'))

        except AttributeError:
            await event.respond(ERROR_MESSAGE_NOT_FROM_PUBLIC, buttons=Button.inline('Назад', b'back_to_main'))

        raise events.StopPropagation


def main():
    """Старт бота. Создание базы данных если ее нет"""

    sql_query(
        """CREATE TABLE IF NOT EXISTS users_data(
        "userid" INT PRIMARY KEY,
        "username" TEXT,
        "is_subscriber" INTEGER DEFAULT 0,
        "time_end_subscription" TEXT,
        "first_time_test_access" INTEGER DEFAULT 1,
        "public" TEXT DEFAULT '',
        "time_send_digest" TEXT
        );"""
    )

    bot.run_until_disconnected()


if __name__ == '__main__':
    main()
