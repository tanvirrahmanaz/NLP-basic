from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# 🔸 Step 1: Input from user
shop_name = input("Enter shop type or name (e.g., coffee shop, pharmacy): ")
location = input("Enter location (e.g., Dhaka, Banani): ")
search_query = f"{shop_name} in {location}"

# 🔸 Step 2: Set up Chrome browser
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # Open full screen
driver = webdriver.Chrome(options=options)

# 🔸 Step 3: Open Google Maps
driver.get("https://www.google.com/maps")
time.sleep(3)

# 🔸 Step 4: Find search box and input query
search_box = driver.find_element(By.ID, "searchboxinput")  # Main search bar
search_box.send_keys(search_query)  # Type our query
search_box.send_keys(Keys.ENTER)  # Hit Enter
time.sleep(5)  # Wait for search results to appear

# 🔸 Step 5: Scroll to load more shops
for _ in range(3):  # Scroll 3 times
    driver.execute_script("document.querySelector('div[role=\"main\"]').scrollBy(0, 1000);")
    time.sleep(2)

# 🔸 Step 6: Collect all shop result cards
places = driver.find_elements(By.CLASS_NAME, "hfpxzc")  # Each card in list view

# 🔸 Step 7: Loop through each shop
for place in places:
    try:
        place.click()  # Click on each shop card
        time.sleep(3)  # Wait for detail panel

        # 🔹 Extract shop name
        name = driver.find_element(By.CLASS_NAME, "DUwDvf").text

        # 🔹 Extract phone number (may not always be there)
        try:
            phone = driver.find_element(By.XPATH, "//button[@data-tooltip='Copy phone number']").text
        except:
            phone = "Phone not found"

        # 🔹 Extract reviews
        try:
            review = driver.find_element(By.CLASS_NAME, "F7nice").text
        except:
            review = "No reviews"

        # 🔹 Print results
        print("Name:", name)
        print("Phone:", phone)
        print("Review:", review)
        print("-" * 40)

        # Go back to list
        driver.back()
        time.sleep(3)
    except Exception as e:
        print("Error:", e)
        continue

# 🔸 Close browser
driver.quit()
