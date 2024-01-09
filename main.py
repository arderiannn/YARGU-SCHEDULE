# -*- coding: utf-8 -*-
import logging
import mysql.connector
import telebot
from telebot import types

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


TELEGRAM_TOKEN = '6527305072:AAE-nILeQ90Moq3FEvvgqbmkFHS5WneV8O0'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

selected_course = None
selected_day = None

@bot.message_handler(commands=['start', 'help', 'привет'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_student = types.KeyboardButton("Студент")
    item_teacher = types.KeyboardButton("Преподаватель")

    markup.add(item_student, item_teacher)

    bot.send_message(message.chat.id, "Доброго времени суток! Вы студент или преподаватель?", reply_markup=markup)

@bot.message_handler(commands=['who'])
def handle_start(message):
    user = message.from_user
    bot.send_message(message.chat.id, f"Привет, {user.first_name}! Я определю кто ты.")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = telebot.types.KeyboardButton("Кто по масти?")
    markup.add(button)
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Студент")
def student_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_choose_group = types.KeyboardButton("Выбор группы")
    item_schedule_calls = types.KeyboardButton("Расписание звонков")

    markup.add(item_choose_group, item_schedule_calls)

    bot.send_message(message.chat.id, "Чем могу помочь?", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Преподаватель")
def teacher_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_choose_group = types.KeyboardButton("Выбор группы")
    item_schedule_calls = types.KeyboardButton("Расписание звонков")
    item_cabinet = types.KeyboardButton("Кабинеты")

    markup.add(item_choose_group, item_schedule_calls, item_cabinet)

    bot.send_message(message.chat.id, "Чем могу помочь?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_selected_room(message):
    global selected_room
    selected_room = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    day_buttons = [types.KeyboardButton(day) for day in days_of_week]
    markup.add(*day_buttons)

    bot.send_message(message.chat.id, "Выберите день недели:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Кабинеты")
def choose_room(message):
    try:
        conn = mysql.connector.connect(user='arderian', password='9Lw-5RV-CRD-Xdn',
                                       host='arderian.mysql.pythonanywhere-services.com', database='arderian$default')

        if conn.is_connected():
            cursor = conn.cursor()

            rooms_query = """
            SELECT DISTINCT RoomNumber FROM arderian$default.schedule;
            """
            cursor.execute(rooms_query)
            rooms = cursor.fetchall()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for room in rooms:
                room_button = types.KeyboardButton(str(room[0]))
                markup.add(room_button)

            back_button = types.KeyboardButton("Вернуться")
            markup.add(back_button)
            bot.send_message(message.chat.id, "Выберите кабинет:", reply_markup=markup)
            cursor.close()
            conn.close()

    except mysql.connector.Error as e:
        print("Ошибка при подключении к базе данных:", e)


@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_selected_room(message):
    global selected_room
    selected_room = message.text
    bot.send_message(message.chat.id, f"Вы выбрали кабинет: {message.text}. Выберите вариант расписания:")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    week_button = types.KeyboardButton("Вся неделя")
    days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    day_buttons = [types.KeyboardButton(day) for day in days_of_week]
    markup.add(week_button, *day_buttons)

    bot.send_message(message.chat.id, "Выберите вариант расписания:", reply_markup=markup)



def get_room_schedule(selected_room, selected_group, selected_day):
    try:
        conn = mysql.connector.connect(user='arderian', password='9Lw-5RV-CRD-Xdn',
                                       host='arderian.mysql.pythonanywhere-services.com', database='arderian$default')

        if conn.is_connected():
            cursor = conn.cursor()
            query = """
                SELECT
                    scheduleID,
                    CourseName AS CourseName,
                    GroupName AS GroupName,
                    LessonNumber,
                    RoomNumber,
                    CASE
                        WHEN NumDen = 'c' THEN 'Числитель'
                        WHEN NumDen = 'z' THEN 'Знаменатель'
                    END AS CombinedInfo,
                    TeacherName
                FROM (
                    SELECT
                        s.scheduleID,
                        c.CourseName,
                        g.GroupName,
                        s.LessonNumber,
                        s.RoomNumber,
                        s.NumDen,
                        t.Name AS TeacherName
                    FROM arderian$default.schedule s
                    JOIN arderian$default.courses c ON s.courseID = c.courseID
                    JOIN arderian$default.groups g ON s.groupID = g.groupID
                    LEFT JOIN arderian$default.teachers t ON c.TeacherID = t.TeacherID
                    WHERE s.RoomNumber = %s AND g.GroupName = %s AND s.DayOfWeek = %s
                    ORDER BY s.LessonNumber
                ) AS SubQuery
                ORDER BY LessonNumber;

            """

            print(f"Selected Room: {selected_room}")
            print(f"Selected Group: {selected_group}")
            print(f"Selected Day: {selected_day}")

            cursor.execute(query, (selected_room, selected_group, selected_day))
            rows = cursor.fetchall()
            print("Fetched Rows:", rows)
            schedule_text = "\n".join([f"Пара {row[3]}, {row[1]}, ауд. {row[4]}, {row[5]}, преподаватель {row[6]}" if row[5] is not None else f"Пара {row[3]}, {row[1]}, ауд. {row[4]}, преподаватель {row[6]}" for row in rows])
            print("Generated Schedule Text:", schedule_text)
            cursor.close()
            conn.close()

            return schedule_text

    except mysql.connector.Error as e:
        print("Ошибка при подключении к базе данных:", e)
        return "Произошла ошибка при получении расписания. Пожалуйста, попробуйте позже."


selected_group = None
selected_day = None

@bot.message_handler(func=lambda message: message.text == "Выбор группы")
def choose_group(message):
    try:
        global selected_group

        conn = mysql.connector.connect(user='arderian', password='9Lw-5RV-CRD-Xdn', host='arderian.mysql.pythonanywhere-services.com', database='arderian$default')

        if conn.is_connected():
            cursor = conn.cursor()
            groups_query = """
            SELECT GroupID, GroupName FROM `groups`;
            """

            cursor.execute(groups_query)
            groups = cursor.fetchall()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for group_id, group_name in groups:
                group_button = types.KeyboardButton(f"{group_name} ({group_id})")
                markup.add(group_button)

            back_button = types.KeyboardButton("Вернуться")
            markup.add(back_button)
            bot.send_message(message.chat.id, "Выберите группу:", reply_markup=markup)

            cursor.close()
            conn.close()

        selected_group = None

    except mysql.connector.Error as e:
        print("Ошибка при подключении к базе данных:", e)


@bot.message_handler(func=lambda message: message.text.endswith(")"))
def handle_selected_group(message):
    global selected_group
    selected_group = message.text
    bot.send_message(message.chat.id, f"Вы выбрали группу: {message.text}. Выберите вариант расписания:")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    week_button = types.KeyboardButton("Вся неделя")
    days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    day_buttons = [types.KeyboardButton(day) for day in days_of_week]
    markup.add(week_button, *day_buttons)
    bot.send_message(message.chat.id, "Выберите вариант расписания:", reply_markup=markup)



@bot.message_handler(func=lambda message: message.text == "Вернуться")
def return_to_main_keyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_choose_group = types.KeyboardButton("Выбор группы")
    item_schedule_calls = types.KeyboardButton("Расписание звонков")

    markup.add(item_choose_group, item_schedule_calls)

    bot.send_message(message.chat.id, "Чем могу помочь?", reply_markup=markup)


@bot.message_handler(func=lambda message: selected_group is not None and message.text in ["Вся неделя", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"])
def handle_schedule_choice(message):
    global selected_group, selected_day
    if message.text == "Вся неделя":
        schedule_text = get_weekly_schedule(selected_group)
        if schedule_text:
            bot.send_message(message.chat.id, schedule_text)
        else:
            bot.send_message(message.chat.id, "Расписание на всю неделю недоступно.")
    else:
        selected_day = message.text
        schedule_text = get_daily_schedule(selected_group, selected_day)

        if schedule_text:
            bot.send_message(message.chat.id, schedule_text)
        else:
            bot.send_message(message.chat.id, f"Расписание на {selected_day.lower()} недоступно.")

    return_to_main_keyboard(message)

def get_daily_schedule(selected_group, selected_day):
    try:
        conn = mysql.connector.connect(user='arderian', password='9Lw-5RV-CRD-Xdn',
                                       host='arderian.mysql.pythonanywhere-services.com', database='arderian$default')

        if conn.is_connected():
            cursor = conn.cursor()
            query = """
            SELECT
                scheduleID,
                CourseName AS CourseName,
                GroupName AS GroupName,
                LessonNumber,
                RoomNumber,
                CASE
                    WHEN NumDen = 'c' THEN 'Числитель'
                    WHEN NumDen = 'z' THEN 'Знаменатель'
                END AS CombinedInfo,
                TeacherName -- Имя преподавателя выводится последним
            FROM (
                SELECT
                    s.scheduleID,
                    c.CourseName,
                    g.GroupName,
                    s.LessonNumber,
                    s.RoomNumber,
                    t.Name AS TeacherName,
                    s.NumDen
                FROM arderian$default.schedule s
                JOIN arderian$default.courses c ON s.courseID = c.courseID
                JOIN arderian$default.groups g ON s.groupID = g.groupID
                LEFT JOIN arderian$default.teachers t ON c.TeacherID = t.TeacherID
                WHERE g.GroupName = %s AND s.DayOfWeek = %s
                ORDER BY s.DayOfWeek, s.LessonNumber
            ) AS SubQuery
            ORDER BY LessonNumber;

            """
            days_of_week = {
                'Понедельник': 'Monday',
                'Вторник': 'Tuesday',
                'Среда': 'Wednesday',
                'Четверг': 'Thursday',
                'Пятница': 'Friday',
                'Суббота': 'Saturday',
                'Воскресенье': 'Sunday'
            }
            # Изменяем значение selected_day на английский день недели, если выбранный день есть в словаре
            if selected_day in days_of_week:
                selected_day = days_of_week[selected_day]
                print('Преобразованнан день недели')
            else:
                 print('нет такого дня недели ')

            # selected_day содержит день недели на английском языке (если найден в словаре)
            text = selected_group
            result = text.split(' ', 1)[0]
            print(result)
            selected_group=result
            print(selected_group, selected_day)
            cursor.execute(query, (selected_group, selected_day))

            rows = cursor.fetchall()
            for row in rows:
                print('строка',row)
                print(str(row[5]))

            schedule_text = "\n".join([f"{row[2]} - Пара {row[3]}, {row[1]}, ауд. {row[4]}, преподаватель {row[6]}\n" if row[5] is None else f"{row[2]} - Пара {row[3]}, {row[1]}, ауд. {row[4]}, {row[5]}, преподаватель {row[6]}\n" for row in rows])

            print('текст',schedule_text)
            cursor.close()
            conn.close()
            return schedule_text

    except mysql.connector.Error as e:
        print("Ошибка при подключении к базе данных:", e)
        return "Произошла ошибка при получении расписания. Пожалуйста, попробуйте позже."


def get_weekly_schedule(selected_group):
    try:
        conn = mysql.connector.connect(user='arderian', password='9Lw-5RV-CRD-Xdn', host='arderian.mysql.pythonanywhere-services.com', database='arderian$default')

        if conn.is_connected():
            cursor = conn.cursor()
            query = """
            SELECT
            scheduleID,
            CourseName AS CourseName,
            GroupName AS GroupName,
            DayOfWeek,
            LessonNumber,
            RoomNumber,
            CASE
                WHEN NumDen = 'c' THEN 'Числитель'
                WHEN NumDen = 'z' THEN 'Знаменатель'
                ELSE NULL
            END AS CombinedInfo,
            TeacherName -- Имя преподавателя выводится последним
        FROM (
            SELECT
                s.scheduleID,
                c.CourseName,
                g.GroupName,
                s.DayOfWeek,
                s.LessonNumber,
                s.RoomNumber,
                sc.NumDen,
                t.Name AS TeacherName -- Выбор имени преподавателя
            FROM arderian$default.schedule s
            JOIN arderian$default.courses c ON s.courseID = c.courseID
            JOIN arderian$default.groups g ON s.groupID = g.groupID
            JOIN arderian$default.teachers t ON c.TeacherID = t.TeacherID -- Связь с таблицей Teachers
            JOIN arderian$default.schedule sc ON sc.scheduleID = s.scheduleID -- Присоединение таблицы schedule для получения NumDen
            WHERE g.GroupName = %s
        ) AS SubQuery
        ORDER BY
            CASE DayOfWeek
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
                ELSE 8
            END,
            LessonNumber;



            """

            text = selected_group
            result = text.split(' ', 1)[0]
            print(result)
            selected_group=result
            cursor.execute(query, (selected_group,))
            rows = cursor.fetchall()
            print(rows)

            schedule_text = ""
            prev_day = None

            for row in rows:
                day_of_week = row[3]
                if day_of_week != prev_day:
                    schedule_text += f"\n{day_of_week}:\n\n"
                    prev_day = day_of_week

                if row[6] is None:
                    schedule_text += f"{row[2]} - Пара {row[4]}, {row[1]}, ауд. {row[5]}, преподаватель {row[7]}\n"
                else:
                    schedule_text += f"{row[2]} - Пара {row[4]}, {row[1]}, ауд. {row[5]}, {row[6]}, преподаватель {row[7]}\n"

            print(schedule_text)

            cursor.close()
            conn.close()

            return schedule_text

    except mysql.connector.Error as e:
        print("Ошибка при подключении к базе данных:", e)
        return "Произошла ошибка при получении расписания. Пожалуйста, попробуйте позже."

#немножко ленимся добавлять в базу
@bot.message_handler(func=lambda message: message.text == "Расписание звонков")
def display_schedule_calls(message):
    schedule_calls_text = "1 пара: [9:00 - 10:35]\n2 пара: [10:45 - 12:20]\n3 пара: [12:30 - 14:05]\n\nПЕРЕРЫВ\n\n4 пара: [15:05 - 16:40]\n5 пара: [16:50 - 18:25]"
    bot.send_message(message.chat.id, schedule_calls_text)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_all(message):
    bot.reply_to(message, message.text)

if __name__ == "__main__":
    bot.polling(none_stop=True)