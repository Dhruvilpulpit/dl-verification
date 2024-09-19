from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

from selenium.webdriver.support import expected_conditions as EC
import time
import requests

app = Flask(__name__)

chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment if you want headless mode

def solve_image_to_text(api_key, img_base64):
    url = "https://api.capsolver.com/createTask"
    payload = {
        "clientKey": api_key,
        "task": {
            "type": "ImageToTextTask",
            "module": "common",
            "body": img_base64,
            "case": True
        }
    }
    response = requests.post(url, json=payload)
    result = response.json()
    if result.get("errorId") == 0:
        return result.get("solution", {}).get("text", "")
    else:
        return f"Error: {result.get('errorDescription', 'Unknown error')}"


# Function to extract table data
def extract_table_data(table_element):
    data = {}
    rows = table_element.find_elements(By.CSS_SELECTOR, "tbody tr")
    for row in rows:
        cols = row.find_elements(By.CSS_SELECTOR, "td")
        if len(cols) >= 2:
            data[cols[0].text.strip()] = cols[1].text.strip()
    return data


@app.route('/get_license_details', methods=['POST'])
def get_license_details():
    # Initialize WebDriver inside the route
    driver = webdriver.Chrome(options=chrome_options)
    
    # Open the website
    driver.get("https://parivahan.gov.in/rcdlstatus/?pur_cd=101")
    # Fill in the form
    dl_number = request.json.get('dl_number')
    dob = request.json.get('dob')

    if not dl_number or not dob:
        return jsonify({"error": "Missing dl_number or dob"}), 400

    driver.find_element(By.XPATH, "//*[@id='form_rcdl:tf_dlNO']").send_keys(dl_number)
    print("hello")
    # Split the date string into day, month, and year
    day, month, year = dob.split('-')


    dob= driver.find_element(By.XPATH,"//*[@id='form_rcdl:tf_dob_input']")
    dob.click()
    # Locate the year dropdown element using the 'By' class and select the year
    dropdown_year = driver.find_element(By.CLASS_NAME, "ui-datepicker-year")
    select_year = Select(dropdown_year)
    select_year.select_by_visible_text(year)  # e.g., '1997'

    # Locate the month dropdown element using the 'By' class and select the month
    dropdown_month = driver.find_element(By.CLASS_NAME, "ui-datepicker-month")
    select_month = Select(dropdown_month)
    select_month.select_by_index(int(month) - 1)  # Month index is zero-based (e.g., '10' becomes 9 for October)

    # Select the day by using an XPath that matches the day
    day_element = driver.find_element(By.XPATH, f"//a[text()='{int(day)}']")
    day_element.click()

    # time.sleep(5)
    # cap_box = driver.find_element(By.XPATH, "//*[@id='form_rcdl:j_idt32:CaptchaID']")
    # cap_box.click()
    # Handle CAPTCHA

    cap_box = driver.find_element(By.XPATH, "//*[@id='form_rcdl:j_idt32:CaptchaID']")
    cap_box.send_keys("")
    time.sleep(1)

    image_element = driver.find_element(By.ID, "form_rcdl:j_idt32:j_idt37")
    base64_string = driver.execute_script("""
        var img = arguments[0];
        var canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, img.width, img.height);
        return canvas.toDataURL('image/png').substring(22);
        """, image_element)

    api_key = "CAP-530C35F199B497178333950FEE0CBE6B"  # Replace with your Capsolver API key
    solved_text = solve_image_to_text(api_key, base64_string)
    print("hello1")
    cap_box = driver.find_element(By.XPATH, "//*[@id='form_rcdl:j_idt32:CaptchaID']")
    print("hello2",solved_text)
    cap_box.send_keys(solved_text)
    
    print("hello3")
    get_detail= driver.find_element(By.XPATH,"//*[@id='form_rcdl:j_idt43']/span")
    print("hello4")
    get_detail.click()
    time.sleep(1)
    # Close the driver once done
    # driver.quit()
    # Extract data (same as before)
    details_of_driving_license = extract_table_data(driver.find_element(By.XPATH, "//div[contains(text(), 'Details Of Driving License:')]/following-sibling::table"))
    initial_details = extract_table_data(driver.find_element(By.XPATH, "//div[contains(text(), 'Driving License Initial Details')]/following-sibling::table"))
    endorsed_details = extract_table_data(driver.find_element(By.XPATH, "//div[contains(text(), 'Driving License Endorsed Details')]/following-sibling::table"))

    validity_details = {}
    validity_details_tables = driver.find_elements(By.XPATH, "//div[contains(text(), 'Driving License Validity Details')]/following-sibling::table")
    for table in validity_details_tables:
        for row in table.find_elements(By.CSS_SELECTOR, "tbody tr"):
            cols = row.find_elements(By.CSS_SELECTOR, "td")
            if len(cols) >= 3:
                validity_details[cols[0].text.strip()] = {
                    "From": cols[1].text.strip(),
                    "To": cols[2].text.strip()
                }

    class_of_vehicle_details = []
    class_table = driver.find_element(By.ID, "form_rcdl:j_idt133")
    rows = class_table.find_elements(By.CSS_SELECTOR, "tbody tr")
    for row in rows:
        cols = row.find_elements(By.CSS_SELECTOR, "td")
        if len(cols) >= 3:
            class_of_vehicle_details.append({
                "COV Category": cols[0].text.strip(),
                "Class Of Vehicle": cols[1].text.strip(),
                "COV Issue Date": cols[2].text.strip()
            })

    data = {
        "Details Of Driving License": details_of_driving_license,
        "Driving License Initial Details": initial_details,
        "Driving License Endorsed Details": endorsed_details,
        "Driving License Validity Details": validity_details,
        "Class Of Vehicle Details": class_of_vehicle_details
    }
    driver.quit()

    return jsonify(data)

if __name__ == '__main__':
    # Run Flask on port 8000 with debug mode enabled
    app.run(port=8000, debug=True)
