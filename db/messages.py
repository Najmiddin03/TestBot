from datetime import datetime, timedelta
import pytz
from config import *


help_msg = """☝️ Mazkur bot testlar yechish maqsadida foydalaniladi. O'qituvchi test yaratadi, o'quvchi esa uni yechadi va natijasini bilib oladi. Quyida botda mavjud komandalar bilan tanishasiz:

<b>Umumiy</b>:
/start - Botni ishga tushirish
/register - Ro'yxatdan o'tish
/myinfo - Shaxsiy ma'lumotlar
/help - Yordam


<b>O'qituvchi</b>:
/create - Test yaratish
/starttest - Yaratilgan testni boshlash
/finishtest - Testni tugatish

<b>O'quvchi</b>:
/solve - Test ishlash
"""

def myinfo_msg(fullname, region, district, school, role):
    role_emoji = "🧑‍🏫" if role == 1 else "🧑‍🎓"
    role_str = "O'qituvchi" if role == 1 else "O'quvchi"
    timezone = pytz.timezone("Asia/Tashkent")
    curr_time = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')
    msg = f"""ℹ️ Sizning ma'lumotlaringiz:
------------------------------------------------------------
👤 Ism: <b>{fullname}</b>

📍 Hudud: <b>{region}</b>
📍 Tuman: <b>{district}</b>

🏫 Maktab: <b>{school}</b>
{role_emoji} Rol: <b>{role_str}</b>
-----------------------------------------------------------
Joriy vaqt: {curr_time}
    """


    return msg



def student_report(fullname, school, testID, student_answers, score, score_p, submitted_at):
    report_msg = f"""👤 Foydalanuvchi: <b>{fullname}</b>
🏫 Maktab: <b>{school}</b>
📖 Test kodi: <b>{test_id_repr(testID)}</b>
✏️ Jami savollar soni: <b>{len(student_answers)} ta</b>
✅ To'g'ri javoblar soni: <b>{score} ta</b>
🔣 Foiz : <b>{score_p}</b> %

🕐 Topshirilgan vaqti: <b>{submitted_at}</b>
    """
    
    return report_msg