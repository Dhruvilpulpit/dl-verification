from flask import Flask, request, jsonify
from selenium import webdriver
import json
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import time
import requests

app = Flask(__name__)

chrome_options = Options()
# chrome_options.add_argument("--headless")  
# Uncomment if you want headless mode

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

# Function to extract data from table
def extract_table_data(table):
    rows = table.find_elements(By.TAG_NAME, 'tr')
    table_data = {}
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        if len(cells) == 2:
            key = cells[0].text.strip()
            value = cells[1].text.strip()
            table_data[key] = value
    return table_data

@app.route('/get_license_details', methods=['POST'])
def get_license_details():
    
    # Specify the path to your ChromeDriver
    chrome_driver_path = "/home/dhruvil/dl verification/chromedriver-linux64/chromedriver"

    # Use Service() to pass the chromedriver path
    service = Service(executable_path=chrome_driver_path)

    # Initialize the WebDriver with Service object and options
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the website
    driver.get("https://parivahan.gov.in/rcdlstatus/?pur_cd=101")
    
    # Fill in the form
    dl_number = request.json.get('dl_number')
    dob = request.json.get('dob')

    if not dl_number or not dob:
        return jsonify({"error": "Missing dl_number or dob"}), 400

    driver.find_element(By.XPATH, "//*[@id='form_rcdl:tf_dlNO']").send_keys(dl_number)
    
    # Split the date string into day, month, and year
    day, month, year = dob.split('-')

    dob_element = driver.find_element(By.XPATH, "//*[@id='form_rcdl:tf_dob_input']")
    dob_element.click()

    # Locate the year dropdown element using the 'By' class and select the year
    dropdown_year = driver.find_element(By.CLASS_NAME, "ui-datepicker-year")
    select_year = Select(dropdown_year)
    select_year.select_by_visible_text(year)

    # Locate the month dropdown element using the 'By' class and select the month
    dropdown_month = driver.find_element(By.CLASS_NAME, "ui-datepicker-month")
    select_month = Select(dropdown_month)
    select_month.select_by_index(int(month) - 1)

    # Select the day by using an XPath that matches the day
    day_element = driver.find_element(By.XPATH, f"//a[text()='{int(day)}']")
    day_element.click()
    print("cheakpoint-1")
    cap_box = driver.find_element(By.XPATH, "/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[3]/input")
    cap_box.send_keys("")
    print("cheakpoint-2")

    time.sleep(1)

    image_element = driver.find_element(By.XPATH, "//*[@id='form_rcdl:j_idt31:j_idt36']")
    print("cheakpoint-3")

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
    
    cap_box = driver.find_element(By.XPATH, "/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[3]/input")
    cap_box.send_keys(solved_text)
    print("cheack box4")
    get_detail = driver.find_element(By.XPATH, "/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/div/button[1]/span")
    get_detail.click()
    time.sleep(1)

    data = {}
    print("cheack box5")

        # Extract details from the "Details Of Driving License" section
    details_of_driving_license = driver.find_element(By.XPATH, "/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table[1]")
    data['Details Of Driving License'] = extract_table_data(details_of_driving_license)
    print("cheack box6")

    # Extract details from the "Driving License Initial Details" section
    initial_details = driver.find_element(By.XPATH, "//div[contains(text(),'Driving License Initial Details')]/following-sibling::table")
    data['Driving License Initial Details'] = extract_table_data(initial_details)
    print("cheack box7")

    # Extract details from the "Driving License Endorsed Details" section
    endorsed_details = driver.find_element(By.XPATH, "//div[contains(text(),'Driving License Endorsed Details')]/following-sibling::table")
    data['Driving License Endorsed Details'] = extract_table_data(endorsed_details)
    print("cheack box8")

    # Extract details from the "Driving License Validity Details" section
    validity_details = driver.find_element(By.XPATH, "//div[contains(text(),'Driving License Validity Details')]/following-sibling::table")
    data['Driving License Validity Details'] = extract_table_data(validity_details)
    print("cheack box9")

    # Extract details from the "Class Of Vehicle Details" section
    class_of_vehicle_details = driver.find_element(By.XPATH, "/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table[4]")
    rows = class_of_vehicle_details.find_elements(By.TAG_NAME, 'tr')
    print("cheack box10")

    class_of_vehicle_data = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        if len(cells) == 3:
            class_of_vehicle_data.append({
                'COV Category': cells[0].text.strip(),
                'Class Of Vehicle': cells[1].text.strip(),
                'COV Issue Date': cells[2].text.strip()
            })
    data['Class Of Vehicle Details'] = class_of_vehicle_data

    # Convert the extracted data to JSON format
    json_data = json.dumps(data, indent=4)

    # Print or save the JSON data
    print(json_data)
    return json_data
    driver.quit()


if __name__ == '__main__':
    # Run Flask on port 8000 with debug mode enabled
    app.run(port=8000, debug=True)
