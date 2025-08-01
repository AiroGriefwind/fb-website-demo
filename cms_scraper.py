import os
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
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
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.NAME, "submit").click()
    time.sleep(3)

    # Login check
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

    # Navigate to Hongkong
    print("\nNavigating to Hongkong section...")
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

    # Click Facebook feature
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
    print(f"Now at Facebook feature page: {driver.current_url}")

    # ----------- Handle custom dropdown and select desired category -----------
    # Wait for custom select to be present (top bar)
    print("Selecting page category in Facebook list...")
    select_span = wait_for_element(
        driver, By.XPATH, '//span[contains(@class,"jcf-select")][not(contains(@class,"jcf-hidden"))]',
        timeout=10
    )
    if not select_span:
        print("Custom select menu not found!")
        driver.quit()
        return

    try:
        select_span.click()  # open the dropdown
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", select_span)

    # Wait for dropdown options to be present (visible)
    print("Dropdown opened, looking for target option...")
    # This XPATH finds the jcf-option span whose text NORMALIZED contains the text you want
    option_text = "1594536350855514 - 巴士的娛圈事"
    dropdown_option = None
    for i in range(10):  # sometimes needs a bit of a loop due to animation
        # Option 1: By exact text content
        dropdown_option = None
        try:
            # Use contains AND strip spaces to be robust
            dropdown_option = wait_for_element(
                driver,
                By.XPATH, f'//span[contains(@class,"jcf-option") and contains(normalize-space(.),"{option_text}")]',
                timeout=2
            )
            if dropdown_option:
                break
        except Exception:
            time.sleep(0.2)
    # Option 2: fallback by data-index (usually "2" for your option)
    if not dropdown_option:
        dropdown_option = wait_for_element(
            driver,
            By.XPATH, '//span[contains(@class,"jcf-option") and @data-index="2"]',
            timeout=2
        )

    if not dropdown_option:
        print("Category option not found in custom dropdown!")
        driver.quit()
        return

        # Store the text BEFORE click, then click
    selected_text = dropdown_option.text.strip()
    print(f"Dropdown category about to select: \"{selected_text}\"")
    try:
        dropdown_option.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", dropdown_option)
    except Exception as e:
        print("Could not select the dropdown option:", e)
        driver.quit()
        return

    time.sleep(2)  # Wait for selection to be applied

    # After click, check the current value of the selector (safe and robust)
    selected_value_element = wait_for_element(
        driver,
        By.XPATH,
        '//span[contains(@class,"jcf-select")][not(contains(@class,"jcf-hidden"))]//span[contains(@class,"jcf-select-text")]//span',
        timeout=5
    )
    if selected_value_element:
        print(f"Dropdown category now selected: \"{selected_value_element.text.strip()}\"")
    else:
        print("Could not find selected value after clicking option.")

    # Optional: Debug check the filter is applied (e.g. an element only present after select)
    print(f"Current URL after dropdown: {driver.current_url}")

    # --------- LOGOUT ---------
    print("\nAttempting logout before closing browser...")
    logout_and_check(driver)

    print("\n👋 Logout (if attempted) done. Closing browser.")
    driver.quit()

if __name__ == "__main__":
    main()
