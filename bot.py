from aiogram import Bot, Dispatcher, executor, types
import aiogram.utils.markdown as fmt
import pymongo
import re
import asyncio
import os
import os.path
import glob
import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from geopy.geocoders import Nominatim
from telegram import ParseMode
from time import sleep
from urllib.request import urlopen
from datetime import datetime
import time
from pytz import timezone
import random
import locale
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

geolocator = Nominatim(user_agent="geoapiExercises")

storage = MemoryStorage()

bot = Bot('5865659864:AAHPPsgTfTtIqOZ2dt6P6UuTwNLuwW6NWCo')
dp = Dispatcher(bot, storage=storage)

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client.BAR_locations
collection = db.bars_prod_2
users = db.users_test
statistics = db.stats_prod

ANSWERS = ['Я советую только по одному бару в день', \
    "42. Это мой лучший ответ, если хочешь следующий бар, приходи завтра", \
    "Тебе не понравился бар, который я написал? Мне похер, я бот!", \
    "Следующий бар завтра", "Попробуй попросить бар с другого аккаунта", \
    "Я устал", "Нужно больше фоток? Вот канал с котиками: https://t.me/brokencats", \
    "Попробуй пообщаться с людьми, у меня только один бар в день.", \
    "Заходи завтра", \
    "Опять работа?", \
    "A pub a day keeps the doctor away", \
    "გაუმარჯოს", "cheerzzz", "Error 0xc00000e, kernel panic, Beep Bop Boop"]

"""from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

inline_btn_1 = InlineKeyboardButton('🍺', callback_data='/drink')
inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1)"""


greeting = """Этот бот поможет тебе выбрать бар в Тбилиси на сегодняшний день, НО ТОЛЬКО ОДИН В ДЕНЬ!

Внимание! Создатели бота НЕ БЕРУТ ДЕНЕГ с заведений за публикацию. Если это изменится, то надпись пропадет.

Над проектом работают:
Alcowalkers: Миша, Юра, Саша, Катя, Егор
Photo: @Meh_21
Text: Юра, Миха, Света
Code: @gleb_miller
Logo: StableDiffusion

Попросить бар можно командой
/bar"""

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    #inline_btn_1 = InlineKeyboardButton('🍺', callback_data='/drink')
    #nline_kb1 = InlineKeyboardMarkup().add(inline_btn_1)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=False)
    markup.add("🍺")
    await message.reply(greeting, reply_markup=markup)


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    if message.chat.id == 98919537 or message.chat.id == 46051043:
        text = "Список команд \
            \n/drink - выбирает случайный бар \
            \n/showall - выводит все записи \
            \n/show BARNAME - выводит информацию о выбраном баре \
            \n/delete BARNAME - удаляет указанный бар из БД \
            \n/patch - запускает процесс изменения записи, запускается без параметров \
            \n/add - запускает процесс добавления бара, запускается без параметров \
            \n/cancel - отменяет процессы добавления или изменения \
            \n/list - выводит список всех названий баров"
    else:
        text = 'Этот бот покажет вам, где сегодня пить в Тбилиси, для этого напиши: \n /drink'
    await bot.send_message(message.chat.id, text)

def add_stats():
    day = datetime.now(timezone('Asia/Tbilisi')).today()
    year_month_day=day.strftime("%Y-%m-%d")
    query = {"year_month_day": year_month_day}
    find_day = list(statistics.find(query))
    print("find_day=", find_day)
    if len(find_day) > 0:
        count = find_day[0]["count"] + 1
        statistics.find_one_and_update({"year_month_day": year_month_day}, {"$set": {"count": count}})
    else:
        insert_data = {"year_month_day": year_month_day, "count": 1}
        statistics.insert_one(insert_data)

def get_today_stats():
    day = datetime.now(timezone('Asia/Tbilisi')).today()
    today = day.strftime("%Y-%m-%d")
    #query = {"day": day"}
    day_stats = list(statistics.find({"year_month_day": today}))
    if day_stats != []:
        return day_stats[0]["count"]
    else:
        return 0

def get_month_stats():
    #day = datetime.now(timezone('Asia/Tbilisi')).today()
    #year_month_day = day.strftime("%Y-%m-%d")
    currentMonth = datetime.now(timezone('Asia/Tbilisi')).month
    currentYear = datetime.now(timezone('Asia/Tbilisi')).year
    if currentMonth < 10:
        check_date=f"{currentYear}-0{currentMonth}"
    else:
        check_date=f"{currentYear}-{currentMonth}"
    count = 0
    all_stats = list(statistics.find())
    for day in all_stats:
        datem = day["year_month_day"][:-3]
        print("datem = ", datem)
        print("check_date =", check_date)
        if datem == check_date:
            count += day["count"]
    return count


def get_all_stats():
    count = 0
    all_stats = list(statistics.find())
    for day in all_stats:
        count += day["count"]
    return count


def check_if_first_time(chatid):
    check_user = list(users.find({"_id": chatid}))
    day = datetime.now(timezone('Asia/Tbilisi')).today()
    print(check_user)
    if len(check_user)>0:
        print(day.date())
        print(check_user[0]["day"].date())
        print(chatid)

        if day.date() == check_user[0]["day"].date():
            return False
        else:
            users.find_one_and_update({"_id": chatid}, {"$set": {"day": day}})
            return True
    else:
        query = {"_id": chatid, "day": day}
        users.insert_one(query)
        return True

async def print_bar(messagechatid, bar):
    name = f"<b>{bar['name']}</b>"
    #print(name)
    description = bar['description']
    lat = bar['lat']
    long = bar['long']
    photo = bar['photo']
    text = description.replace("BARNAME", name)
    if "." in bar['link']:
        part1 = text[:text.rfind("LINK")]
        part2 = text[text.rfind("LINK")+4:]
        change = part1[part1.rfind(' '):]
        link = f"<a href='{bar['link']}'> {change}</a>"
        text = part1.replace(change, link) + part2

    now = datetime.now()
    TODAY = now.strftime("%A")
    
    text = text.replace("TODAY", TODAY)  
    print("text= ", text)
    
    await bot.send_photo(messagechatid, photo, name, parse_mode=ParseMode.HTML)
    await bot.send_message(messagechatid, text, parse_mode=ParseMode.HTML)
    await bot.send_location(messagechatid, lat, long)

@dp.message_handler(lambda message: message.text and '🍺' in message.text)
async def drink(message: types.Message):

    if check_if_first_time(message.chat.id):
        all_bars = list(collection.find())
        number = random.randint(0, len(all_bars)-1)
        print(number)
        bar = all_bars[number]
        add_stats()
        await print_bar(message.chat.id, bar)
    else:
        await bot.send_message(message.chat.id, random.choice(ANSWERS))



@dp.message_handler(drink, commands=['drink', 'bar', 'pub', 'go', 'start', 'beer', 'pivo', 'drunk', 'tbilisi'])
async def drink2(message: types.Message):

    if check_if_first_time(message.chat.id):
        all_bars = list(collection.find())
        number = random.randint(0, len(all_bars)-1)
        print(number)
        bar = all_bars[number]
        add_stats()
        await print_bar(message.chat.id, bar)
    else:
        all_bars = list(collection.find())
        print(len(all_bars))
        await bot.send_message(message.chat.id, random.choice(ANSWERS))

@dp.message_handler(commands=['showall'])
async def showall(message: types.Message):
    if message.chat.id == 98919537 or message.chat.id == 46051043:
        all_bars = list(collection.find())
        for bar in all_bars:
            await print_bar(message.chat.id, bar)
            sleep(2)

@dp.message_handler(commands=['list'])
async def list_all_bars(message: types.Message):
    if message.chat.id == 98919537 or message.chat.id == 46051043:
        all_bars = list(collection.find())
        text = ""
        for bar in all_bars:
            text += bar["name"]+"\n"
        await message.reply(text)
        

@dp.message_handler(commands=['show'])
async def delete(message: types.Message):
    if message.chat.id == 98919537 or message.chat.id == 46051043:
        text = message.text.replace("/show ", "")
        print('text =', text)
        query = {"name": f"{text}"}
        bar = list(collection.find(query))
        print(bar)
        if len(bar)>0:
            await print_bar(message.chat.id, bar[0])


@dp.message_handler(commands=['delete'])
async def delete(message: types.Message):
    if message.chat.id == 98919537 or message.chat.id == 46051043:
        text = message.text.replace("/delete ", "")
        print('text =', text)
        query = {"name": f"{text}"}
        print(list(collection.find()))
        print(query)
        collection.delete_one(query)
        await bot.send_message(message.chat.id, "удалено")


@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    if message.chat.id == 98919537 or message.chat.id == 46051043:
        #text = message.text.replace("/delete ", "")
        today_stats = get_today_stats()
        month_stats = get_month_stats()
        all_stats = get_all_stats()
        
        await bot.send_message(message.chat.id, f"сегодня помог найти бар {today_stats} людям")
        await bot.send_message(message.chat.id, f"за месяц помог найти бар {month_stats} людям")
        await bot.send_message(message.chat.id, f"всего помог найти бар {all_stats} людям")



class Form(StatesGroup):
    text = State()
    link = State()
    pic = State()
    loc = State()
    name = State()
    patches = State()
    button = State()

@dp.message_handler(commands='patch')
async def cmd_patch(message: types.Message):
    
    if message.chat.id == 98919537 or message.chat.id == 46051043:
        await Form.name.set()
        await message.reply("Введите название бара для изменения")


@dp.message_handler(state=Form.name)
async def start_patch(message: types.Message, state: FSMContext):
    
    async with state.proxy() as data:
        data['name'] = message.text
 
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True)
    markup.add("description", "photo", "location", "link")
    await Form.button.set()
    await message.reply("Что поправить?", reply_markup=markup)


@dp.message_handler(content_types=['any'], state=Form.button)
async def finish_patch(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['type'] = message.text
        #print(data['type'])
        query = {"name": f"{data['name']}"}
        bar = list(collection.find(query))
        if len(bar) == 0:
            await message.reply("Таких баров нет", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
        else:
            if data['type'] == "description" or data['type'] == "link":
                text_to_send = bar[0][data['type']]
                await message.reply(f"Старое значение \n{text_to_send}", reply_markup=types.ReplyKeyboardRemove())

                await Form.patches.set()
                await message.reply("отправьте изменения")

            else:
                await Form.patches.set()
                await message.reply("отправьте изменения", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types=['any'], state=Form.patches)
async def finish_patch(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        #data['type'] = message.text
        query = {"name": f"{data['name']}"}
        bar = list(collection.find(query))
        if len(bar) == 0:
            await message.reply("Таких баров нет")
            await state.finish()
        else:
            bar_id = bar[0]["_id"]

            if data['type'] == "description":
                description = message.text
                
                collection.find_one_and_update({"_id": bar_id}, {"$set": {"description": description}})
            
            if data['type'] == "link":
                link = message.text
                
                collection.find_one_and_update({"_id": bar_id}, {"$set": {"link": link}})

            if data['type'] == "photo":
                photo = message["photo"][-1]["file_id"]
                collection.find_one_and_update({"_id": bar_id}, {"$set": {"photo": photo}})

            if data['type'] == "location":
                if message['location']:
                    data['loc'] = message['location']
                    lat = data['loc']["latitude"]
                    long = data['loc']["longitude"]
                else:
                    lat, long = message.text.split(",")
                    long = long.strip()

                """location = geolocator.reverse(
                    str(lat) + "," + str(long), language='ru')
                s = str(location.address)
                
                l = [i.strip() for i in s.split(',')]
                
                
                city = l[2].replace('городской округ ', '')
                country = l[-1]
                """

                city = 'Tbilisi'
                country = 'Georgia'

                collection.find_one_and_update({"_id": bar_id}, {"$set": {"country": country, "city": city, "lat": lat, "long": long}})
    await message.reply("изменено")
    await state.finish()


@dp.message_handler(state='*', commands='cancel')
async def cancel_handler(message: types.Message, state: FSMContext):
        
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    
    await state.finish()
    
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())
    
    

@dp.message_handler(commands='add')
async def cmd_start(message: types.Message):
    
    if message.chat.id == 98919537 or message.chat.id == 46051043:
        await Form.text.set()
        await message.reply("Введите название и описание локации через запятую")
    


@dp.message_handler(state=Form.text)
async def process_text(message: types.Message, state: FSMContext):
    
    async with state.proxy() as data:
        data['text'] = message.text
 
    await message.reply("Отправьте ссылку")
    await Form.link.set()

@dp.message_handler(state=Form.link)
async def process_text(message: types.Message, state: FSMContext):
    
    async with state.proxy() as data:
        data['link'] = message.text
    
    await message.reply("Отправьте фото")
    await Form.pic.set()
    
@dp.message_handler(content_types=['photo'], state=Form.pic)
async def process_photo(message: types.Message, state: FSMContext):
    
    async with state.proxy() as data:
        data["file_id"] = message["photo"][-1]["file_id"]
        
    await message.reply("Отправьте геолокацию")
    await Form.loc.set()    
    

@dp.message_handler(content_types=['any'], state=Form.loc)
async def process_loc(message: types.Message, state: FSMContext):
    print(message)
    async with state.proxy() as data:
        text_list = [i.strip() for i in data['text'].split(',')]
       
        name = text_list[0]
        description = ''
        if len(text_list) > 1:
            description = ', '.join(text_list[1:])
            print(description)
        
        if message['location']:
            data['loc'] = message['location']
            lat = data['loc']["latitude"]
            long = data['loc']["longitude"]
        else:
            lat, long = message.text.split(",")
            long = long.strip()

        """location = geolocator.reverse(
            str(lat) + "," + str(long), language='ru')
        s = str(location.address)
        
        l = [i.strip() for i in s.split(',')]
        
        city = l[2].replace('городской округ ', '')
        country = l[-1]
        """
        country = "Georgia"
        city = 'Tbilisi'
        

        values = {'name': name, 'country': country, 'city': city,
            'lat': lat, 'long': long, 'description': description, "link": data["link"], "photo": data["file_id"]}
        x = collection.insert_one(values)
    await message.reply("добавлено")
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    
