import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options # Options import 추가
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def crawl_cu():
    """
    CU 편의점의 1+1 행사 상품 정보를 크롤링합니다.
    :return: 상품 정보가 담긴 딕셔너리의 리스트
    """
    print("WebDriver를 설정합니다 (헤드리스 모드)...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options) # options 인자 전달
    print("WebDriver 설정 완료.")

    products_data = []
    total_found = 0
    try:
        url = "https://cu.bgfretail.com/event/plus.do?category=event&depth2=1&sf=N"
        print(f"'{url}' 페이지로 이동합니다...")
        driver.get(url)

        WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "li.prod_list")) > 0)
        print("초기 상품 목록 로드를 확인했습니다.")

        print("모든 상품을 로드하기 위해 JavaScript 함수를 직접 호출합니다...")
        while True:
            try:
                current_count = len(driver.find_elements(By.CSS_SELECTOR, "li.prod_list"))
                driver.execute_script("nextPage(1);")
                WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "li.prod_list")) > current_count)
                print(f"상품 개수 증가 확인: {current_count} -> {len(driver.find_elements(By.CSS_SELECTOR, 'li.prod_list'))}")
                time.sleep(1)
            except (TimeoutException, NoSuchElementException):
                print("더 이상 상품을 로드할 수 없어 '더보기' 루프를 종료합니다.")
                break
            except Exception as e:
                print(f"처리 중 예기치 않은 오류 발생: {e}")
                break

        print("\n모든 상품의 컨텐츠가 로드되도록 페이지를 아래로 스크롤합니다...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("페이지 스크롤 완료.")
                break
            last_height = new_height

        print("\n페이지에 로드된 모든 상품 정보 추출을 시작합니다...")
        products = driver.find_elements(By.CSS_SELECTOR, "li.prod_list")
        total_found = len(products)
        print(f"총 {total_found}개의 상품을 찾았습니다. 데이터 수집을 시작합니다.")
        print("-" * 30)

        for i, product_element in enumerate(products):
            try:
                name = product_element.find_element(By.CSS_SELECTOR, ".name p").text
                price_str = product_element.find_element(By.CSS_SELECTOR, ".price strong").text
                if not price_str:
                    continue
                image_url = product_element.find_element(By.CSS_SELECTOR, "img.prod_img").get_attribute("src")
                event_type = product_element.find_element(By.CSS_SELECTOR, ".badge span").text
                
                product_info = {
                    "brand": "CU",
                    "name": name,
                    "price": int(price_str.replace(',', '')),
                    "image_url": image_url,
                    "event_type": event_type,
                }
                products_data.append(product_info)
            except NoSuchElementException:
                continue
    
    except Exception as e:
        print(f"[오류] CU 크롤링 중 예외가 발생했습니다: {e}")
    
    finally:
        print("WebDriver를 종료합니다.")
        driver.quit()

    print(f"\n--- CU 크롤링 완료: 총 {len(products_data)}개 수집 (발견: {total_found}개) ---")
    return products_data
