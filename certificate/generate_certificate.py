from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from db import requests
from db.config import LOGS_CHANNEL

def generate_certificate(studentID, testID):
    try:
        template_path = "certificate0.jpg"
        font_path = "OpenSans-Regular.ttf"

        # Open the certificate template
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size

        student_name = requests.get_user_data(userID)[0]
        subject_name = requests.get_user_data(subject_name)[0]
        current_time = datetime.now().strftime('%Y-%m-%d')


        # Define text positions (adjust as needed)
        time_x = width * 0.43
        time_y = height * 0.76

        font_size = 50
        font_color = (0, 0, 0)

        font_name = ImageFont.truetype(font_path, 65)
        font_subject_name = ImageFont.truetype(font_path, font_size)
        font_date = ImageFont.truetype(font_path, font_size)

        student_text_width = draw.textlength(student_name, font=font_name)
        student_text_height = draw.textlength(student_name, font=font_name)

        subject_text_width = draw.textlength(subject_name, font=font_subject_name)
        subject_text_height = draw.textlength(subject_name, font=font_subject_name)

        student_name_x = width // 2 - student_text_width // 4
        student_name_y = height // 2.3

        subject_name_x = width * 0.34
        subject_name_y = height * 0.2

        # Draw text on the image
        draw.text((student_name_x, student_name_y), student_name, fill=font_color, font=font_name)
        draw.text((subject_name_x, subject_name_y), subject_name, fill=font_color, font=font_subject_name)
        draw.text((time_x, time_y), f"{current_time}", fill=font_color, font=font_date)

        # Save the modified image
        current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        new_image_path = f"certificate0-{current_datetime}.jpg"
        img.save(new_image_path)
        print(f"Certificate saved as: {new_image_path}")

        return new_image_path
    except Exception as e:
        print(f"Error in Generating Certificate: {e}")
        # For Telegram bot: bot.send_message(LOGS_CHANNEL, f"Error in Generating Certificate: {e}")

# Test the function
if __name__ == '__main__':
    generate_certificate(1, 1)
