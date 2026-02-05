import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def crawl_emart24():
    """
    E-Mart24의 지정된 카테고리별로 모든 행사 상품을 수집합니다.
    """
    print("WebDriver를 설정합니다 (헤드리스 모드)...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("WebDriver 설정 완료.")

    products_data = []
    processed_product_names = set()
    categories_to_crawl = ["간편식사", "과자", "음료", "생활용품"]

    try:
        base_url = "https://emart24.co.kr/goods/event"

        for category_name in categories_to_crawl:
            print(f"\n--- 카테고리 '{category_name}' 크롤링 시작 ---")
            driver.get(base_url)

            try:
                category_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, category_name))
                )
                driver.execute_script("arguments[0].click();", category_link)
                time.sleep(2) # 카테고리 변경 후 페이지 로드 대기
            except TimeoutException:
                print(f"  - 카테고리 '{category_name}'를 찾을 수 없어 건너뜁니다.")
                continue

            page_num = 1
            while True:
                print(f"  - {page_num} 페이지 수집 중 (현재 총 {len(products_data)}개)...")
                
                try:
                    wait_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".itemWrap"))
                    )
                except TimeoutException:
                    print("  - 상품 목록을 찾을 수 없어 수집을 종료합니다.")
                    break

                products = driver.find_elements(By.CSS_SELECTOR, ".itemWrap")
                for product in products:
                    try:
                        name = product.find_element(By.CSS_SELECTOR, ".itemtitle p a").text
                        if name not in processed_product_names:
                            price_str = product.find_element(By.CSS_SELECTOR, ".price").text.replace(',', '').replace('원', '').strip()
                            image_url = product.find_element(By.CSS_SELECTOR, ".itemSpImg img").get_attribute("src")
                            event_type = "N/A"
                            try:
                                event_element = product.find_element(By.CSS_SELECTOR, ".itemTit > span:not([style*='opacity: 0'])")
                                event_type = event_element.text
                            except NoSuchElementException:
                                pass

                            products_data.append({
                                "brand": "E-Mart24",
                                "name": name,
                                "price": int(price_str),
                                "image_url": image_url,
                                "event_type": event_type,
                                "category": category_name, # 카테고리 이름 추가
                            })
                            processed_product_names.add(name)
                    except Exception:
                        continue
                
                try:
                    next_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".pageNationWrap .nextButtons .next"))
                    )
                    driver.execute_script("arguments[0].click();", next_button)
                    WebDriverWait(driver, 10).until(EC.staleness_of(wait_element))
                    page_num += 1
                except (NoSuchElementException, TimeoutException):
                    print("  - '다음' 버튼을 찾을 수 없어 현재 카테고리의 수집을 종료합니다.")
                    break
    
    except Exception as e:
        print(f"[오류] E-Mart24 크롤링 중 예외가 발생했습니다: {e}")
    
    finally:
        print("WebDriver를 종료합니다.")
        driver.quit()

    print(f"\n--- E-Mart24 크롤링 완료: 총 {len(products_data)}개 수집 ---")
    return products_data
