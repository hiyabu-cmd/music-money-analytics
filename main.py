from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# Streamlit app URL
STREAMLIT_URL = os.environ.get("STREAMLIT_APP_URL", "https://music-money-analytics-6w38qnsrdok58yvctt3x5a.streamlit.app/")

def main():
    print("----------------------------------------------------------------")
    print("Starting Strict Wake-Up Script")
    print("----------------------------------------------------------------")

    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(STREAMLIT_URL)
        print(f"Page loaded: {driver.title}")
        time.sleep(5) # Give it 5 seconds purely to load DOM

        # 1. Try to find the Wake Up Button
        try:
            # Look for button specifically
            wake_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Yes, get this app back up')]"))
            )
            print("⚠️ SLEEPING STATUS DETECTED: 'Wake Up' button found.")
            
            # FORCE CLICK via JavaScript (more reliable than standard .click())
            driver.execute_script("arguments[0].click();", wake_btn)
            print("ACTION: Clicked the button using JavaScript.")
            
            # Wait for reaction
            time.sleep(10)
            print("Waited 10s for boot-up sequence.")

        except:
            print("INFO: 'Wake Up' button was NOT found. Checking if app is already running...")

        # 2. Strict Verification - Check for YOUR App Content
        # We look for something that ONLY exists when your app is actually running.
        # Based on your previous prompts, your table likely has "Channel Name" or "Video Name"
        
        page_source = driver.page_source
        
        if "Channel Name" in page_source or "Video Name" in page_source or "Music Money" in page_source:
            print("✅ SUCCESS: App content detected. The website is awake and running.")
        else:
            # If we don't see the button AND we don't see the app content, WE FAIL.
            print("❌ FAILURE: Could not find 'Wake Up' button, but also could not find app content.")
            print("Dumping first 500 characters of page source for debugging:")
            print(page_source[:500])
            exit(1) # Force GitHub Action to fail (Red X)

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
