import os
import tempfile
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from functools import wraps

from dotenv import load_dotenv
load_dotenv()

# ============================ CONFIG =================================

LOGIN_URL = os.getenv("CMS_LOGIN_URL")
ADMIN_URL = os.getenv("CMS_ADMIN_URL")
USERNAME = os.getenv("CMS_USERNAME")
PASSWORD = os.getenv("CMS_PASSWORD")

# =================== RETRY LOGIC =====================================

def retry_step(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        driver = kwargs.get("driver")
        max_tries = 3
        last_exc = None
        for i in range(max_tries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                print(f"⚠️ Step [{func.__name__}] failed (attempt {i+1}/{max_tries}): {e}")
                if driver:
                    try:
                        img = driver.get_screenshot_as_file(f"fail_{func.__name__}_try{i+1}.png")
                    except Exception:
                        pass
                time.sleep(2)
        print(f"❌ Step [{func.__name__}] failed after {max_tries} attempts: {last_exc}")
        raise last_exc
    return wrapper

# =================== STEPS ===========================================

@retry_step
def login(driver, wait):
    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.NAME,"username"))).send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.NAME, "submit").click()
    time.sleep(2)
    # Confirm login
    if not driver.current_url.startswith(ADMIN_URL):
        raise Exception("Not redirected to admin page after login.")
    # Check for login success
    span = wait.until(EC.presence_of_element_located((By.ID,"login-username")))
    if "Hello FB Autopost!" not in span.text:
        raise Exception("Did not see expected dashboard greeting.")
    print("✅ Login successful.")

@retry_step
def go_to_hongkong(driver, wait):
    link = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "/admin/sites/features.php?site=hongkong")]')))
    link.click()
    time.sleep(2)
    print("✅ Arrived at Hongkong page.")

@retry_step
def go_to_facebook(driver, wait):
    fb_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "/admin/facebook/?site=hongkong")]')))
    fb_link.click()
    time.sleep(2)
    print("✅ Arrived at Facebook feature page.")

@retry_step
def select_category(driver, wait, category_text="1594536350855514 - 巴士的娛圈事"):
    select_span = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[contains(@class,"jcf-select")][not(contains(@class,"jcf-hidden"))]')))
    select_span.click()
    time.sleep(1)
    dropdown_option = None
    for _ in range(8):  # Wait a bit for animation
        try:
            dropdown_option = driver.find_element(
                By.XPATH,
                f'//span[contains(@class,"jcf-option") and contains(normalize-space(.),"{category_text}")]'
            )
            break
        except NoSuchElementException:
            time.sleep(0.3)
    if not dropdown_option:
        raise Exception(f"Could not find dropdown category: {category_text}")
    sel_text = dropdown_option.text.strip()
    dropdown_option.click()
    time.sleep(1)
    # Confirm it visually
    selected_value_element = wait.until(EC.presence_of_element_located((
        By.XPATH, '//span[contains(@class,"jcf-select")][not(contains(@class,"jcf-hidden"))]//span[contains(@class,"jcf-select-text")]//span'
    )))
    print(f"✅ Selected dropdown value: {selected_value_element.text.strip()}")
    return sel_text

@retry_step
def logout(driver, wait):
    try:
        avatar_btn = wait.until(EC.element_to_be_clickable((By.ID, "navbar-user")))
        avatar_btn.click()
        time.sleep(1)
        logout_btn = wait.until(EC.element_to_be_clickable((By.ID, "logout")))
        logout_btn.click()
        time.sleep(1)
        wait.until(EC.presence_of_element_located((By.NAME, "username")))
        print("✅ Logout successful.")
    except Exception as e:
        print("⚠️ Logout failed or already logged out:", e)
        # No raise: safe quit

# ============ MAIN CONTROLLER ========================================

def main():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Enable if you do not want a UI
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
    wait = WebDriverWait(driver, 12)

    final_exception = None
    try:
        print("==[ STEP: LOGIN ]==")
        login(driver, wait)
        print("==[ STEP: NAV TO HONGKONG ]==")
        go_to_hongkong(driver, wait)
        print("==[ STEP: NAV TO FACEBOOK ]==")
        go_to_facebook(driver, wait)
        print("==[ STEP: SELECT CATEGORY ]==")
        select_category(driver, wait)
        print("🎉 All navigation steps succeeded! (Insert scraping logic here...)")

    except Exception as e:
        print("❌ Encountered error during automation:", e)
        final_exception = e
    finally:
        try:
            print("==[ STEP: LOGOUT BEFORE EXIT ]==")
            logout(driver, wait)
        except Exception as e2:
            print("Logout failed:", e2)
        print("==[ QUITTING BROWSER ]==")
        driver.quit()
        if final_exception:
            print("==[ FULL TRACE ]==")
            print(traceback.format_exc())
            raise final_exception

if __name__ == "__main__":
    main()
