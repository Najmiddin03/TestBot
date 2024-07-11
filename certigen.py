from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from config import *
from db import requests
import os

from aiogram.types import FSInputFile

async def generate_certificate(studentID, testID):
    try:
        template_path = f"{prod_dir}assets/images/certificate.png"
        font_path = f"{prod_dir}assets/fonts/OpenSans-Regular.ttf"

        # Open the certificate template
        img = Image.open(template_path)

        draw = ImageDraw.Draw(img)
        width, height = img.size

        student_name = await requests.user_is_registered(studentID)
        print(student_name)
        st_name = student_name[0]
        teacher_name = await requests.get_teacher_name(testID)
        current_time = datetime.now().strftime('%Y-%m-%d')

        # Define text positions (adjust as needed)
        # name_x = width * 0.37  # 20% from left side
        # name_y = height * 0.5  # 60% from top

        time_x = width * 0.26  # Same position as name
        time_y = height * 0.76  # Slightly below name

        font_size = 32
        font_color = (0, 0, 0) 

        font_name = ImageFont.truetype(font_path, 56)
        font_teacher_name = ImageFont.truetype(font_path, font_size)
        font_date = ImageFont.truetype(font_path, font_size)


        student_text_width = draw.textlength(st_name, font=font_name)
        student_text_height = draw.textlength(st_name, font=font_name)

        teacher_text_width = draw.textlength(teacher_name, font=font_name)
        teacher_text_height = draw.textlength(teacher_name, font=font_name)

        student_name_x = width // 2 - student_text_width // 2
        student_name_y = height // 2

        teacher_name_x = width * 0.63
        teacher_name_y = height * 0.76


        # Draw text on the image
        draw.text((student_name_x, student_name_y), st_name, fill=font_color, font=font_name)
        draw.text((teacher_name_x, teacher_name_y), teacher_name, fill=font_color, font=font_teacher_name)
        draw.text((time_x, time_y), f"{current_time}", fill=font_color, font=font_date)

        # Option 1: Save the modified image (user downloads manually)
        current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        new_image_path = f"{prod_dir}assets/images/certificate-{current_datetime}.png"
        img.save(new_image_path)
        print(f"Certificate saved as: {new_image_path}")
        inputfile_img = FSInputFile(new_image_path)

        
        await bot.send_document(studentID, inputfile_img, caption="🎉 Sertifikatni yuklab oling.")
        os.remove(new_image_path)
    except Exception as e:
            print(f"Error in Generating Certificate: {e}")
            return None