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
    print("Starting Strict Wake-Up Script (Long Wait Version)")
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
        time.sleep(5) 

        # --- STEP 1: WAKE UP THE APP ---
        try:
            wake_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Yes, get this app back up')]"))
            )
            print("⚠️ SLEEPING STATUS DETECTED: 'Wake Up' button found.")
            driver.execute_script("arguments[0].click();", wake_btn)
            print("ACTION: Clicked the button using JavaScript.")
            
        except:
            print("INFO: 'Wake Up' button not found. App might already be loading or awake.")

        # --- STEP 2: WAIT FOR CONTENT (POLLING) ---
        # Wait up to 90 seconds (18 checks * 5 seconds) for the app to load
        print("Waiting for app to finish booting up (this can take ~60 seconds)...")
        
        max_retries = 18
        success = False
        
        for i in range(max_retries):
            page_source = driver.page_source
            
            # Check for specific keywords from your user table
            if "Channel Name" in page_source or "Video Name" in page_source or "Music Money" in page_source:
                print(f"✅ SUCCESS: App content detected on attempt #{i+1}!")
                success = True
                break
            
            print(f"Attempt {i+1}/{max_retries}: Content not ready yet. Waiting 5s...")
            time.sleep(5)

        if not success:
            print("❌ FAILURE: Timed out waiting for app content to load.")
            # Optional: Print page title to see if it's stuck on 'Streamlit' or an error
            print(f"Final Page Title: {driver.title}") 
            exit(1) # Fail the Action

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
