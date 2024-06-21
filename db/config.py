import os

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

DB_HOST = "localhost"
DB_USER = "root"        # Your MySQL username
DB_PASSWORD = "5656"  # Your MySQL password
DB_NAME = "test2"  # The database you created

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = '6029491691:AAFchAuoZT3OVTy4aSI_6ntVSnI7JxVaGWk'

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

LOGS_CHANNEL = os.getenv("LOGS_CHANNEL")

roles = ["O'qituvchi", "O'quvchi"]
regions = {
    "Toshkent shahri": ["Olmazor tumani", "Shayxontohur tumani", "Uchtepa tumani", "Chilonzor tumani", "Yunusobod tumani", "Mirobod tumani", "Yashnobod tumani", "Yakkasaroy tumani", "Sergeli tumani", "Bektemir tumani", "Yangihayot tumani", "Mirzo Ulug'bek tumani"],
    "Toshkent viloyati": ["Bekobod tumani", "Bo'ka tumani", "Bo'stonliq tumani", "Chinoz tumani", "Ohangaron tumani", "Oqqo'rg'on tumani", "O'rta Chirchiq tumani", "Parkent tumani", "Piskent tumani", "Qibray tumani", "Quyi Chirchiq tumani", "Toshkent tumani", "Yangiyo'l tumani", "Yuqori Chirchiq tumani", "Zangiota tumani"],
    "Andijon viloyati": ["Ulug'nor tumani", "Baliqchi tumani", "Bo'ston tumani", "Shahrixon tumani", "Oltinko'l tumani", "Asaka tumani", "Marhamat tumani", "Buloqboshi tumani", "Andijon tumani", "Xo'jaobod tumani", "Jalaquduq tumani", "Qo'rg'ontepa tumani", "Xonobod tumani", "Andijon shahri"],
    "Namangan viloyati": ["Namangan tumani", "Mingbuloq tumani", "Kosonsoy tumani", "Pop tumani", "To'raqo'rg'on tumani", "Uychi tumani", "Chortoq tumani", "Yangiqo'rg'on tumani", "Norin tumani", "Uchqo'rg'on tumani", "Chust tumani", "Namangan shahri tumani", "Namangan shahri"],
    "Farg'ona viloyati": ["Oltiariq tumani", "Bag'dod tumani", "Beshariq tumani", "Buvayda tumani", "Dang'ara tumani", "Farg'ona tumani", "Furqat tumani", "Qo'shtepa tumani", "Quva tumani", "Rishton tumani", "So'x tumani", "Toshloq tumani", "Uchko'prik tumani", "O'zbekiston tumani", "Yozyovon tumani", "Farg'ona shahri"],
    "Sirdaryo viloyati": ["Oqoltin tumani", "Boyovut tumani", "Guliston tumani", "Xovos tumani", "Mirzaobod tumani", "Sayxunobod tumani", "Sardoba tumani", "Sirdaryo tumani", "Yangiyer tumani", "Shirin tumani", "Guliston shahri"],
    "Jizzax viloyati": ["Arnasoy tumani", "Baxmal tumani", "Do'stlik tumani", "Forish tumani", "G'allaorol tumani", "Sharof Rashidov tumani", "Mirzacho'l tumani", "Paxtakor tumani", "Yangiobod tumani", "Zomin tumani", "Zafarobod tumani", "Zarbdor tumani", "Jizzax shahri"],
    "Samarqand viloyati": ["Bulung'ur tumani", "Ishtixon tumani", "Jomboy tumani", "Kattaqo'rg'on tumani", "Qo'shrabot tumani", "Narpay tumani", "Nurobod tumani", "Oqdaryo tumani", "Paxtachi tumani", "Payariq tumani", "Pastdarg'om tumani", "Samarqand tumani", "Toyloq tumani", "Urgut tumani", "Samarqand shahri"],
    "Qashqadaryo viloyati": ["Chiroqchi", "Dehqonobod", "G'uzor", "Qamashi", "Qarshi", "Koson", "Kasbi", "Kitob", "Mirishkor", "Muborak", "Nishon", "Shahrisabz", "Yakkabog'", "Ko'kdala", "Qarshi shahri"],
    "Surxondaryo viloyati": ["Angor tumani", "Boysun tumani", "Denov tumani", "Jarqo'rg'on tumani", "Qiziriq tumani", "Qumqo'rg'on tumani", "Muzrabot tumani", "Oltinsoy tumani", "Sariosiyo tumani", "Sherobod tumani", "Sho'rchi tumani", "Termiz tumani", "Uzun tumani", "Termiz shahri"],
    "Navoiy viloyati": ["Konimex tumani", "Karmana tumani", "Qiziltepa tumani", "Xatirchi tumani", "Navbahor tumani", "Nurota tumani", "Tomdi tumani", "Uchquduq tumani", "Navoiy shahri"],
    "Buxoro viloyati": ["Olot tumani", "Buxoro tumani", "G'ijduvon tumani", "Jondor tumani", "Kogon tumani", "Qorako'l tumani", "Qorovulbozor tumani", "Peshku tumani", "Romitan tumani", "Shofirkon tumani", "Vobkent tumani", "Buxoro shahri"],
    "Xorazm viloyati": ["Bog'ot tumani", "Gurlan tumani", "Xonqa tumani", "Hazorasp tumani", "Xiva tumani", "Qo'shko'pir tumani", "Shovot tumani", "Urganch tumani", "Yangiariq tumani", "Yangibozor tumani", "Tuproqqal'a tumani", "Urganch shahri"],
    "Qoraqalpog'iston Respublikasi": ["Amudaryo tumani", "Beruniy tumani", "Chimboy tumani", "Ellikqal'a tumani", "Kegeyli tumani", "Mo'ynoq tumani", "Nukus tumani", "Qanliko'l tumani", "Qo'ng'irot tumani", "Qorao'zak tumani", "Shumanay tumani", "Taxtako'pir tumani", "To'rtko'l tumani", "Xo'jayli tumani", "Taxiatosh tumani", "Bo'zatov tumani", "Nukus shahri"]
}


button_names = {
    "myinfo": "👤 Mening ma'lumotlarim",
    "help": "🆘 Yordam",
    "create": "📝 Test yaratish",
    "solve": "/solve"
}

# Buttons
menu_buttons = [types.KeyboardButton(button_names["myinfo"]), types.KeyboardButton(button_names["help"]), types.KeyboardButton(button_names["create"])]
student_menu = [types.KeyboardButton(button_names["myinfo"]), types.KeyboardButton(button_names["help"]), types.KeyboardButton(button_names["solve"])]
start_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
start_keyboard.add(*menu_buttons)  
student_start_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
student_start_kb.add(*student_menu)  

test_create_again_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
test_create_again_markup.add(types.KeyboardButton(button_names["create"]))

solve_again_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
solve_again_markup.add(types.KeyboardButton(button_names['solve']))


def test_id_repr(testID):
    # This method converts integer test ID to string representation: 12 -> 000012
    return "0"*(6-len(str(testID)))+str(testID)
