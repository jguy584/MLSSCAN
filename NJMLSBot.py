import time
import hashlib
from twilio.rest import Client
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from PIL import Image, ImageChops, ImageStat
import pytesseract
import re
import os
import io
#from plyer import notification
import random
from datetime import datetime

def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text

def extract_info(text):
    mls_pattern = r"MLS\s?#\s?(\d+)"
    mls_match = re.search(mls_pattern, text)
    mls_number = mls_match.group(1) if mls_match else None

    top_line = text.split('\n')[0].strip()

    return mls_number, top_line

def take_screenshot(driver, url, folder_path, retry_delay=300):
    while True:
        try:
            driver.get(url)
            time.sleep(8)  # Add a delay of 8 seconds

            # Get the dimensions of the page
            width = driver.execute_script("return Math.max(document.body.scrollWidth, document.body.offsetWidth, document.documentElement.clientWidth, document.documentElement.scrollWidth, document.documentElement.offsetWidth);")
            height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")

            # Calculate the dimensions of the desired screenshot size
            left, upper, right, lower = 0, 700, 280, 900

            # Take screenshot and crop it to the desired size
            png = driver.get_screenshot_as_png()
            full_screenshot = Image.open(io.BytesIO(png))
            cropped_screenshot = full_screenshot.crop((left, upper, right, lower))

            # Save the cropped screenshot
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cropped_screenshot.save(f"{folder_path}/screenshot_{timestamp}.png")

            return cropped_screenshot

        except selenium.common.exceptions.TimeoutException:
            print("Timeout occurred, retrying in {} seconds...".format(retry_delay))
            time.sleep(retry_delay)

def crop_image(image, left, upper, right, lower):
    return image.crop((left, upper, right, lower))

def image_difference(image1, image2):
    diff = ImageChops.difference(image1, image2)
    return ImageStat.Stat(diff).mean[0]

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--remote-debugging-port=9222')

    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1024, 2048)  # Add this line to set the window size
    
    return driver

def check_site_for_changes(url, folder_path, threshold, to_phone_number, from_phone_number, account_sid, auth_token):
    driver = create_driver()
    previous_mls_number = None
    previous_top_line = None

    while True:
        current_screenshot = take_screenshot(driver, url, folder_path)
        text = extract_text_from_image(current_screenshot)
        current_mls_number, current_top_line = extract_info(text)
        print(f'MLS#: {current_mls_number}')
        print(f'Cost and loc.: {current_top_line}')


        if previous_mls_number:
            if current_mls_number != previous_mls_number:
                send_sms_notification(to_phone_number, from_phone_number, f"The website has been updated! {current_top_line}", account_sid, auth_token)
            else:
                print("The MLS number is the same!")
                
        previous_mls_number = current_mls_number
        previous_top_line = current_top_line
        time.sleep(random.randint(30, 122))


#def check_site_for_changes(url, folder_path, threshold, to_phone_number, from_phone_number, account_sid, auth_token):
    driver = create_driver()
    previous_screenshot = None

    while True:
        current_screenshot = take_screenshot(driver, url, folder_path)
        
        SStext = extract_text_from_image(current_screenshot)
        print(SStext)

        if previous_screenshot:
            diff = image_difference(current_screenshot, previous_screenshot)
            if diff > threshold:
                send_sms_notification(to_phone_number, from_phone_number, "The website has been updated!", account_sid, auth_token)
            else:
                print("The image looks the same!")
                
        previous_screenshot = current_screenshot
        time.sleep(random.randint(30, 122))

def send_sms_notification(to_phone_number, from_phone_number, message_body, account_sid, auth_token):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=message_body,
        from_=from_phone_number,
        to=to_phone_number
    )
    print(f"SMS sent. SID: {message.sid}")

if __name__ == "__main__":
    # Replace these with the website you want to monitor and your Twilio details
    url_to_check = "https://www.njmls.com/listings/index.cfm?zoomlevel=0&action=dsp.results&page=1&display=30&sortBy=newest&newest&isFuzzy=false&location=&city=&state=&county=&zipcode=07410&radius=3&proptype=%2C4&maxprice=&minprice=&beds=0&baths=0&dayssince=&newlistings=&pricechanged=&keywords=&mls_number=&garage=&basement=&fireplace=&pool=&laundry=&elevator=&fitnesscenter=&furnished=&shortterm=&dogsallowed=&catsallowed=&earliestdate=&latestdate=&yearBuilt=&building=&officeID=&openhouse=&countysearch=false&ohdate=&style=&rerun=25-05-2022&rerundate=25-05-2022&searchname=CloseBy&backtosearch=false&token=false&searchid=&searchcountid=&&status=A&ss=1&rerun=14/18/23&rerundate=15/25/22&searchid=101659"
    to_phone_number = "+1"
    from_phone_number = "+1833..."
    account_sid = ""
    auth_token = ""

check_site_for_changes(url_to_check, "/media/john/Terra/TESTSHOTS", 0.2, to_phone_number, from_phone_number, account_sid, auth_token)
