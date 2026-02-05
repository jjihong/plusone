import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def run_comparison_test():
    print("WebDriver를 설정합니다 (헤드리스 모드)...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1920x1080")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("WebDriver 설정 완료.")

    # --- 1. CU 사이트 테스트 ---
    print("\n--- [테스트 1/2] 성공했던 CU 사이트 접속 시도 ---")
    try:
        url_cu = "https://cu.bgfretail.com/event/plus.do?category=event&depth2=1&sf=N"
        print(f"'{url_cu}' 페이지로 이동합니다...")
        driver.get(url_cu)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.prod_list")))
        print(">> 결과: 성공! CU 상품 목록을 10초 안에 찾았습니다.")
    except Exception as e:
        print(f">> 결과: 실패. CU 사이트에서 오류가 발생했습니다: {e}")

    # --- 2. GS25 사이트 테스트 ---
    print("\n--- [테스트 2/2] 문제가 발생했던 GS25 사이트 접속 시도 ---")
    try:
        url_gs25 = "http://gs25.gsretail.com/gscvs/ko/products/event-goods"
        print(f"'{url_gs25}' 페이지로 이동합니다...")
        driver.get(url_gs25)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul#paramList li")))
        print(">> 결과: 성공! GS25 상품 목록을 10초 안에 찾았습니다.")
    except Exception as e:
        print(f">> 결과: 실패. GS25 사이트에서 오류가 발생했습니다: {e}")

    print("\nWebDriver를 종료합니다.")
    driver.quit()
    print("\n테스트가 완료되었습니다.")
    # 이 테스트 함수는 별도의 데이터를 반환하지 않습니다.
    return True
