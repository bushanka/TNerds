import sqlite3


def sql_query(command_text, data_base_name='src/database/users_data.db', params=None):
    """Функция для отправки SQL запросов"""
    connection = False
    data = None
    try:
        connection = sqlite3.connect(data_base_name)
        cursor = connection.cursor()
        if params is None:
            cursor.execute(command_text)
            data = cursor.fetchall()
        else:
            cursor.execute(command_text, params)
            data = cursor.fetchall()
        connection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if connection:
            connection.close()
    return data
