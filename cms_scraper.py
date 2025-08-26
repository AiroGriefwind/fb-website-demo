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

import json
import datetime
import pytz
import re
from selenium.webdriver.common.action_chains import ActionChains

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

def login(driver, wait):
    driver.get(LOGIN_URL)
    time.sleep(2)  # let redirect settle

    try:
        # Try to find login form
        username_box = driver.find_elements(By.NAME, "username")
        if username_box:
            username_box[0].send_keys(USERNAME)
            driver.find_element(By.NAME, "password").send_keys(PASSWORD)
            driver.find_element(By.NAME, "submit").click()
            time.sleep(2)
        else:
            print("Username input not found: already logged in or different page.")
    except Exception as e:
        print("Failed to fill login form:", e)
    
    # Now, confirm we're on the admin or homepage regardless of how we got there
    try:
        # Wait for a unique post-login element, e.g., "Hongkong" button
        wait.until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/admin/sites/features.php?site=hongkong")]')))
        print("✅ Reached admin/homepage after login/redirect")
    except Exception as e:
        print("Login may have failed. Dumping diagnostic info...")
        dump_html_and_screenshot(driver)
        raise

def dump_html_and_screenshot(driver, prefix="login_fail"):
    import datetime
    nowstr = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sspath = f"{prefix}_{nowstr}.png"
    htmlpath = f"{prefix}_{nowstr}.html"
    driver.save_screenshot(sspath)
    with open(htmlpath, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"Saved screenshot to {sspath} and HTML to {htmlpath}")


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
def select_category(driver, wait, category_text="巴士的娛圈事"):
    select_span = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[contains(@class,"jcf-select")][not(contains(@class,"jcf-hidden"))]')))
    select_span.click()
    time.sleep(1)
    dropdown_option = None
    for _ in range(8):
        try:
            dropdown_option = driver.find_element(
                By.XPATH, f'//span[contains(@class,"jcf-option") and contains(normalize-space(.),"{category_text}")]'
            )
            break
        except NoSuchElementException:
            time.sleep(0.3)
    if not dropdown_option:
        raise Exception(f"Could not find dropdown category: {category_text}")
    sel_text = dropdown_option.text.strip()
    dropdown_option.click()
    time.sleep(1)
    selected_value_element = wait.until(EC.presence_of_element_located((
        By.XPATH, '//span[contains(@class,"jcf-select")][not(contains(@class,"jcf-hidden"))]//span[contains(@class,"jcf-select-text")]//span'
    )))
    print(f"✅ Selected dropdown value: {selected_value_element.text.strip()}")
    print("✅ Selected dropdown value. Waiting 30 seconds for full post list to load...")
    time.sleep(30)
    return sel_text

HKT = pytz.timezone("Asia/Hong_Kong")
TIME_RE = re.compile(r"\b\d{2}-\d{2} \d{2}:\d{2} (AM|PM)\b")

def parse_hk_datetime(date_str, now_year):
    try:
        dt = datetime.datetime.strptime(date_str, "%m-%d %I:%M %p")
        full_dt = dt.replace(year=now_year)
        return HKT.localize(full_dt)
    except Exception as e:
        print("Failed to parse datetime:", date_str, e)
        return None

def extract_time_text(li):
    try:
        time_elem = li.find_element(By.XPATH, './/div[contains(@class,"text-holder")]//span[last()]')
        txt = (time_elem.get_attribute("textContent") or "").strip()
        m = TIME_RE.search(txt)
        if m:
            return m.group(0)
    except Exception:
        pass
    # Try all spans under text-holder
    for s in li.find_elements(By.XPATH, './/div[contains(@class,"text-holder")]//span'):
        txt = (s.get_attribute("textContent") or "").strip()
        m = TIME_RE.search(txt)
        if m:
            return m.group(0)
    return ""

@retry_step
def scroll_and_scrape_posts(driver, wait, max_hours=48, outfile="fb_posts.json"):
    print(f"==[ SCRAPING FB POSTS, WITHIN LAST {max_hours} HOURS ]==")
    postlist_ul = wait.until(EC.presence_of_element_located((
        By.XPATH, '//ul[contains(@class,"fan-page-list")]'
    )))

    posts = []
    seen_post_ids = set()
    load_more = True
    last_post_time = None
    first_run = True

    ACTION = ActionChains(driver)
    now_hkt = datetime.datetime.now(HKT)
    min_time = now_hkt - datetime.timedelta(hours=max_hours)
    print(f"Scrape window: {min_time} -> {now_hkt}")

    consecutive_no_growth = 0
    last_li_count = 0

    while load_more:
        li_elems = postlist_ul.find_elements(By.XPATH, './li[contains(@class,"fan-page-card")]')
        new_count = 0
        for li in li_elems:
            try:
                # Ensure card is visible for JS-populated fields
                driver.execute_script("arguments[0].scrollIntoView({block:'center'})", li)
                for _ in range(8):
                    update_time_str = extract_time_text(li)
                    if update_time_str:
                        break
                    time.sleep(0.25)
                if not update_time_str:
                    continue

                title_elem = li.find_element(By.XPATH, './/div[contains(@class,"text-holder")]/p')
                title_text = title_elem.text.strip()

                post_dt = parse_hk_datetime(update_time_str, now_hkt.year)
                if not post_dt:
                    continue
                # Stop if posts are older than threshold
                if post_dt < min_time:
                    load_more = False
                    print(f"Post earlier than window: {title_text} ({update_time_str})")
                    break

                footer_elem = li.find_element(By.XPATH, './/div[contains(@class,"post-footer-icons")]')
                reached_num = None
                engaged_num = None
                for s in footer_elem.find_elements(By.XPATH, './span'):
                    lab = s.find_element(By.XPATH, './small').text
                    val_txt = s.text.split('\n')[0].replace(',', '').strip()
                    if lab == "reached":
                        reached_num = int(val_txt) if val_txt.isdigit() else val_txt
                    if lab == "engaged":
                        engaged_num = int(val_txt) if val_txt.isdigit() else val_txt
                postid = li.get_attribute('data-postid') or hash(title_text + update_time_str)
                if postid in seen_post_ids:
                    continue
                seen_post_ids.add(postid)
                posts.append({
                    "title": title_text,
                    "datetime": post_dt.strftime("%Y-%m-%d %H:%M"),
                    "timestamp": int(post_dt.timestamp()),
                    "reached": reached_num,
                    "engaged": engaged_num,
                    "raw_time": update_time_str,
                })
                new_count += 1
            except Exception as e:
                continue

        # If hit threshold, finish
        if not load_more:
            break

        # Heuristic: keep scrolling while new cards are loaded AND we have not seen a post older than the threshold
        if len(li_elems) == last_li_count:
            consecutive_no_growth += 1
        else:
            consecutive_no_growth = 0
        last_li_count = len(li_elems)
        if consecutive_no_growth >= 2:
            print("No more new posts after two scroll attempts. Ending scrape.")
            break

        first_run = False
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", postlist_ul)
        time.sleep(1.5)

    with open(outfile, "w", encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(posts)} posts to {outfile}")
    return posts

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

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Enable if you do not want a UI
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
        print("==[ STEP: SCRAPE POSTS ]==")
        scroll_and_scrape_posts(driver, wait, max_hours=48, outfile="fb_posts_last48h.json")
        print("==[ SCRAPE FINISHED ]==")

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
