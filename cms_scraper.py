import os
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # If dotenv not installed, skip

LOGIN_URL = os.getenv("CMS_LOGIN_URL")
ADMIN_URL = os.getenv("CMS_ADMIN_URL")
USERNAME = os.getenv("CMS_USERNAME")
PASSWORD = os.getenv("CMS_PASSWORD")

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Add this line to use a unique temp directory for Chrome user data
    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })

    print("Opening login page...")
    driver.get(LOGIN_URL)
    time.sleep(2)

    # Fill login form
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.NAME, "submit").click()
    time.sleep(3)

    # Check for login success
    success = False
    if driver.current_url.startswith(ADMIN_URL):
        try:
            span = driver.find_element(By.ID, "login-username")
            if "Hello FB Autopost!" in span.text:
                print("Login successful!")
                success = True
            else:
                print("Login span found, but text does not match.")
        except NoSuchElementException:
            print("Login span not found.")
    else:
        print(f"Login failed, current URL: {driver.current_url}")

    if not success:
        driver.quit()
        exit(1)

    # --- Manual inspection countdown ---
    print("\n" + "="*60)
    print("🚨 Browser will stay open for 30 seconds for manual inspection.")
    print("⌨️  Copy the URL or inspect the page as needed.")
    print("="*60)
    for i in range(30, 0, -1):
        print(f"Closing browser in {i} seconds...", end='\r')
        time.sleep(1)
    print("\n👋 Countdown finished. Closing browser.")
    driver.quit()

if __name__ == "__main__":
    main()