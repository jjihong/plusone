from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# StaleElementReferenceException에 대응하는 커스텀 대기 클래스
class wait_for_page_number_to_change:
    def __init__(self, locator, old_text):
        self.locator = locator
        self.old_text = old_text

    def __call__(self, driver):
        try:
            new_text = driver.find_element(*self.locator).text
            return new_text != self.old_text
        except StaleElementReferenceException:
            # 요소가 stale 상태이면, 페이지가 변경되고 있다는 의미이므로, 잠시 후 다시 시도하게 함
            return False

def crawl_seven_eleven():
    """
    네이버 검색 결과를 기반으로 세븐일레븐 행사 상품을 수집합니다.
    - 대분류 탭을 순회하며 모든 상품 정보를 수집합니다.
    """
    print("WebDriver를 설정합니다 (디버깅 모드, 헤드리스 비활성화)...")
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("WebDriver 설정 완료.")

    products_data = []
    processed_products = set()

    try:
        url = "https://m.search.naver.com/search.naver?where=m&sm=mtb_etc&mra=bjZF&qvt=0&query=%EC%84%B8%EB%B8%90%EC%9D%BC%EB%A0%88%EB%B8%90%20%ED%96%89%EC%82%AC"
        print(f"'{url}' 페이지로 이동합니다...")
        driver.get(url)
        time.sleep(3) # 초기 로드 대기

        main_categories = ["음료", "아이스크림", "과자", "간편식사", "생활용품"]
        
        for main_cat_name in main_categories:
            print(f"\n--- 대분류 '{main_cat_name}' 크롤링 시작 ---")
            try:
                main_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//ul[contains(@class, 'tab_list')]//a[span[text()='{main_cat_name}']]"))
                )
                driver.execute_script("arguments[0].click();", main_tab)
                time.sleep(2) # 탭 변경 후 데이터 로드 대기
            except TimeoutException:
                print(f"  - 대분류 탭 '{main_cat_name}'을 찾을 수 없어 건너뜁니다.")
                continue

            # 페이지네이션 루프
            page_num = 1
            while True:
                print(f"  - {page_num} 페이지 수집 중 (현재 총 {len(products_data)}개)...")
                
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='list'] > li[role='listitem']"))
                    )
                except TimeoutException:
                    print("    - 상품 목록을 찾을 수 없어 현재 탭의 수집을 종료합니다.")
                    break

                products = driver.find_elements(By.CSS_SELECTOR, "ul[role='list'] > li[role='listitem']")
                for product in products:
                    try:
                        name = product.find_element(By.CSS_SELECTOR, "strong.item_name span.name_text").text
                        event_type = "N/A"
                        try:
                            event_type = product.find_element(By.CSS_SELECTOR, "strong.item_name span.ico_event").text
                        except NoSuchElementException:
                            pass

                        if (name, main_cat_name, event_type) in processed_products:
                            continue

                        price_str = product.find_element(By.CSS_SELECTOR, "p.item_price em").text.replace(',', '')
                        image_url = product.find_element(By.CSS_SELECTOR, "a.thumb img").get_attribute('src')

                        products_data.append({
                            "brand": "7-Eleven",
                            "name": name,
                            "price": int(price_str),
                            "image_url": image_url,
                            "category": main_cat_name,
                            "event_type": event_type,
                        })
                        processed_products.add((name, main_cat_name, event_type))
                    except StaleElementReferenceException:
                        print("    - Stale element를 만나 상품 하나를 건너뜁니다. 목록이 갱신되었을 수 있습니다.")
                        continue
                    except (NoSuchElementException, ValueError):
                        continue
                
                # '다음' 버튼으로 페이지네이션 (Stale Element에 대응하는 커스텀 대기 사용)
                try:
                    current_page_element = driver.find_element(By.CSS_SELECTOR, "strong.cmm_npgs_now._current")
                    current_page_num = current_page_element.text
                    
                    next_button = driver.find_element(By.CSS_SELECTOR, "a.cmm_pg_next.on")
                    driver.execute_script("arguments[0].click();", next_button)

                    WebDriverWait(driver, 10).until(
                        wait_for_page_number_to_change((By.CSS_SELECTOR, "strong.cmm_npgs_now._current"), current_page_num)
                    )
                    page_num += 1
                except (NoSuchElementException, TimeoutException):
                    print("    - '다음' 버튼을 찾을 수 없거나 페이지 번호 변경을 감지할 수 없어 현재 탭의 수집을 종료합니다.")
                    break

    except Exception as e:
        print(f"[오류] 7-Eleven 크롤링 중 예외가 발생했습니다: {e}")
    
    finally:
        print("WebDriver를 종료합니다.")
        driver.quit()

    return products_data