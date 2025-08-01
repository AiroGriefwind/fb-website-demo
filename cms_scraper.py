import os
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LOGIN_URL = os.getenv("CMS_LOGIN_URL")
ADMIN_URL = os.getenv("CMS_ADMIN_URL")
USERNAME = os.getenv("CMS_USERNAME")
PASSWORD = os.getenv("CMS_PASSWORD")
BASE_URL = LOGIN_URL.split('/login')[0]  # a base for building absolute links

def wait_for_element(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        return None

def logout_and_check(driver):
    try:
        avatar_btn = wait_for_element(driver, By.ID, "navbar-user", timeout=5)
        if not avatar_btn:
            print("Cannot find avatar button for logout.")
            return False
        avatar_btn.click()
        time.sleep(1)
    except Exception as ex:
        print(f"Error opening dropdown: {ex}")
        return False
    try:
        logout_btn = wait_for_element(driver, By.ID, "logout", timeout=5)
        if not logout_btn:
            print("Logout button not found in dropdown.")
            return False
        logout_btn.click()
    except Exception as ex:
        print(f"Error clicking logout: {ex}")
        return False
    time.sleep(2)
    login_box = wait_for_element(driver, By.NAME, "username", timeout=10)
    if login_box:
        print("Logout completed, login form detected.")
        return True
    else:
        print("Logout failed: login form not detected after logout click.")
        return False

def main():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })

    print("Opening login page...")
    driver.get(LOGIN_URL)
    time.sleep(2)

    # Login
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

    # --------- CLICK "Hongkong" BUTTON ---------
    print("\nNavigating to Hongkong section...")
    # Find 'a' with href containing '/admin/sites/features.php?site=hongkong'
    hongkong_link = wait_for_element(
        driver, By.XPATH, '//a[contains(@href, "/admin/sites/features.php?site=hongkong")]'
    )
    if not hongkong_link:
        print("Hongkong site link not found.")
        driver.quit()
        return

    hongkong_link.click()
    time.sleep(2)
    print(f"At: {driver.current_url}")

    # --------- CLICK "Facebook" FEATURE ---------
    print("Navigating to Facebook feature...")
    facebook_link = wait_for_element(
        driver, By.XPATH, '//a[contains(@href, "/admin/facebook/?site=hongkong")]'
    )
    if not facebook_link:
        print("Facebook feature link not found.")
        driver.quit()
        return

    facebook_link.click()
    time.sleep(2)

    print("Final page reached!")
    print(f"Current URL: {driver.current_url}")
    print(f"Page title: {driver.title}")

    # --------- LOGOUT ---------
    print("\nAttempting logout before closing browser...")
    logout_and_check(driver)

    print("\n👋 Logout (if attempted) done. Closing browser.")
    driver.quit()

if __name__ == "__main__":
    main()
