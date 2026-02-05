import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def crawl_gs25():
    """
    GS25의 '전체' 탭에서 모든 행사 상품을 수집합니다.
    - 무한 루프 방지 기능이 포함된 안정적인 페이지네이션 로직을 사용합니다.
    """
        print("WebDriver를 설정합니다 (헤드리스 모드)...")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("window-size=1920x1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("WebDriver 설정 완료.")

    products_data = []
    processed_product_names = set() # 중복 수집 및 무한루프 방지를 위한 세트

    try:
        url = "http://gs25.gsretail.com/gscvs/ko/products/event-goods"
        print(f"'{url}' 페이지로 이동합니다...")
        driver.get(url)
        
        # 크롤링 시작 전, '전체' 탭을 명시적으로 클릭하여 모든 상품을 대상으로 설정
        try:
            print("--- '전체' 탭을 선택합니다 ---")
            total_tab_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a#TOTAL"))
            )
            driver.execute_script("arguments[0].click();", total_tab_link)
            # 탭 전환 후 상품 목록이 갱신될 때까지 잠시 대기
            time.sleep(2)
            print("--- '전체' 탭 선택 완료 ---")
        except TimeoutException:
            print("오류: '전체' 탭을 시간 내에 찾거나 클릭할 수 없습니다. 기본 탭에서 크롤링을 시작합니다.")

        # 페이지네이션 루프
        page_num = 1
        while True:
            print(f"  - {page_num} 페이지 수집 중 (현재 총 {len(products_data)}개)...")
            
            try:
                # 페이지 변경 감지 및 상품 목록 로드를 위한 기준 요소(첫 번째 상품)
                wait_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.prod_list li:first-child"))
                )
            except TimeoutException:
                print("  - 상품 목록을 찾을 수 없어 수집을 종료합니다.")
                break
            
            # 현재 페이지의 첫 상품 이름이 이미 처리되었다면, 무한 루프 상태로 보고 종료
            first_product_name = wait_element.find_element(By.CSS_SELECTOR, "p.tit").text
            if first_product_name in processed_product_names:
                print("  - 이전에 처리된 페이지와 내용이 동일하여 수집을 종료합니다.")
                break

            # 현재 페이지의 모든 상품을 수집
            products = driver.find_elements(By.CSS_SELECTOR, "ul.prod_list li")
            for product in products:
                try:
                    name = product.find_element(By.CSS_SELECTOR, "p.tit").text
                    if name not in processed_product_names:
                        price_str = product.find_element(By.CSS_SELECTOR, "span.cost").text.replace(',', '').replace('원', '')
                        image_url = product.find_element(By.CSS_SELECTOR, "p.img > img").get_attribute("src")
                        event_type = product.find_element(By.CSS_SELECTOR, "div.flag_box span").text.strip()
                        
                        products_data.append({
                            "brand": "GS25", "name": name, "price": int(price_str),
                            "image_url": image_url, "event_type": event_type,
                        })
                        processed_product_names.add(name)
                except Exception:
                    continue
            
            # 다음 페이지로 이동
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, ".paging a.next")
                driver.execute_script("arguments[0].click();", next_button)
                
                # 페이지가 실제로 변경될 때까지 대기 (이전 페이지의 첫 상품 요소가 사라질 때까지)
                WebDriverWait(driver, 10).until(EC.staleness_of(wait_element))
                
                page_num += 1
            except (NoSuchElementException, TimeoutException):
                print("  - '다음' 버튼을 찾을 수 없거나 페이지 전환에 실패하여 수집을 종료합니다.")
                break
    
    except Exception as e:
        print(f"[오류] GS25 크롤링 중 예외가 발생했습니다: {e}")
    
    finally:
        print("WebDriver를 종료합니다.")
        driver.quit()

    print(f"\n--- GS25 크롤링 완료: 총 {len(products_data)}개 수집 ---")
    return products_data
