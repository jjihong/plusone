import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
            return False

def crawl_all():
    """
    네이버 '편의점 행사' 검색 결과를 기반으로, 카테고리별로 모든 편의점의 행사 상품을 수집합니다.
    """
    print("WebDriver를 설정합니다 (헤드리스 모드)...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1")
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("WebDriver 설정 완료.")

    products_data = []
    processed_products = set()

    try:
        base_url = "https://m.search.naver.com/search.naver?where=m&sm=mtb_etc&mra=bjZF&qvt=0&query=%ED%8E%B8%EC%9D%98%EC%A0%90%ED%96%89%EC%82%AC"
        main_categories = ["음료", "아이스크림", "과자", "간편식사", "생활용품"]
        
        for main_cat_name in main_categories:
            print(f"\n--- 카테고리 '{main_cat_name}' 크롤링 시작 ---")
            driver.get(base_url)
            
            try:
                # 1. 클릭할 카테고리 탭의 링크(a) 요소를 찾음
                tab_link_xpath = "//ul[contains(@class, 'tab_list')]//a[span[text()='{}']]".format(main_cat_name)
                main_tab_link = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, tab_link_xpath))
                )
                
                # 2. 표준 .click() 메서드를 사용 (실제 사용자 클릭과 가장 유사)
                main_tab_link.click()
                
                # 3. 최종 확인 로직: 부모 li 태그의 aria-selected 속성이 'true'가 될 때까지 대기
                parent_li_xpath = "//ul[contains(@class, 'tab_list')]//li[a/span[text()='{}']]".format(main_cat_name)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, parent_li_xpath + "[@aria-selected='true']"))
                )
                print(f"  - '{main_cat_name}' 탭이 성공적으로 활성화되었습니다.")

            except TimeoutException:
                print(f"  - 카테고리 탭 '{main_cat_name}'을 클릭하거나 활성화하는 데 실패했습니다. 다음 카테고리로 넘어갑니다.")
                continue

            # 페이지네이션 루프
            page_num = 1
            consecutive_duplicate_pages = 0
            while True:
                print(f"  - {page_num} 페이지 수집 중 (현재 총 {len(products_data)}개)...")
                is_page_new = False

                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='list'] > li[role='listitem']")))
                except TimeoutException:
                    print("    - 상품 목록을 찾을 수 없어 현재 탭의 수집을 종료합니다.")
                    break

                products = driver.find_elements(By.CSS_SELECTOR, "ul[role='list'] > li[role='listitem']")
                for product in products:
                    try:
                        name = product.find_element(By.CSS_SELECTOR, "strong.item_name span.name_text").text
                        scraped_brand = product.find_element(By.CSS_SELECTOR, "span.store_info").text
                        
                        if (name, scraped_brand) in processed_products:
                            continue
                        
                        is_page_new = True
                        event_type = "N/A"
                        try:
                            event_type = product.find_element(By.CSS_SELECTOR, "strong.item_name span.ico_event").text
                        except NoSuchElementException: pass
                        
                        image_url = product.find_element(By.CSS_SELECTOR, "a.thumb img").get_attribute('src')
                        
                        sale_price, original_price = None, None
                        try:
                            sale_price_str = product.find_element(By.CSS_SELECTOR, "p.item_price em").text.replace(',', '').replace('원', '').strip()
                            sale_price = int(sale_price_str)
                            original_price_str = product.find_element(By.CSS_SELECTOR, "p.item_price span.item_discount").text.replace(',', '').replace('원', '').strip()
                            original_price = int(original_price_str)
                        except NoSuchElementException:
                            original_price = sale_price
                        except (ValueError, AttributeError): continue

                        products_data.append({"brand": scraped_brand, "name": name, "sale_price": sale_price, "original_price": original_price, "image_url": image_url, "category": main_cat_name, "event_type": event_type})
                        processed_products.add((name, scraped_brand))
                    except (StaleElementReferenceException, NoSuchElementException, ValueError): continue
                
                if not is_page_new and page_num > 1:
                    consecutive_duplicate_pages += 1
                    print(f"    - 경고: {consecutive_duplicate_pages}번째 새로운 상품 없는 페이지 발견.")
                else:
                    consecutive_duplicate_pages = 0
                
                if consecutive_duplicate_pages >= 3:
                    print("    - 3번 연속으로 새로운 상품이 없는 페이지가 발견되어 수집을 종료합니다.")
                    break
                
                try:
                    current_page_num = driver.find_element(By.CSS_SELECTOR, "strong.cmm_npgs_now._current").text
                    next_button = driver.find_element(By.CSS_SELECTOR, "a.cmm_pg_next.on")
                    driver.execute_script("arguments[0].click();", next_button)
                    WebDriverWait(driver, 10).until(wait_for_page_number_to_change((By.CSS_SELECTOR, "strong.cmm_npgs_now._current"), current_page_num))
                    page_num += 1
                except (NoSuchElementException, TimeoutException):
                    print("    - '다음' 버튼을 찾을 수 없어 현재 탭의 수집을 종료합니다.")
                    break
    except Exception as e:
        print(f"[오류] 통합 크롤러 실행 중 예외가 발생했습니다: {e}")
    finally:
        print("WebDriver를 종료합니다.")
        driver.quit()
    return products_data