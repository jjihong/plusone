import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def crawl_naver_events():
    print("WebDriver를 설정합니다...")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    print("WebDriver 설정 완료.")

    products_data = []
    try:
        initial_url = "https://m.search.naver.com/search.naver?sm=mtp_hty.top&where=m&query=%ED%8E%B8%EC%9D%98%EC%A0%90+%ED%96%89%EC%82%AC"
        print(f"'{initial_url}' 페이지로 이동합니다...")
        driver.get(initial_url)

        events_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".sc.cs_convenience_store"))
        )
        
        # 드롭다운 메뉴에서 선택할 브랜드 이름 목록을 먼저 추출
        select_element = Select(events_section.find_element(By.CSS_SELECTOR, "select.slct"))
        brand_names = [opt.text for opt in select_element.options if opt.text != "전체"]
        print(f"수집 대상 브랜드: {brand_names}")

        for brand_name in brand_names:
            print(f"\n>> '{brand_name}' 브랜드를 선택합니다...")
            # 매번 페이지가 바뀌므로, 섹션과 드롭다운을 다시 찾습니다.
            events_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".sc.cs_convenience_store"))
            )
            select_element = Select(events_section.find_element(By.CSS_SELECTOR, "select.slct"))
            
            # '사람처럼' 드롭다운 메뉴에서 텍스트로 브랜드를 선택
            select_element.select_by_visible_text(brand_name)
            
            # 페이지가 전환되고, 새로운 브랜드 섹션이 로드될 때까지 기다립니다.
            # url_contains: URL에 선택한 브랜드 이름(쿼리)이 포함될 때까지 기다림
            WebDriverWait(driver, 15).until(EC.url_contains(brand_name))
            print(f"  - '{brand_name}' 브랜드 페이지 로드 완료.")
            
            # 이제 이 페이지 내에서 행사 탭을 순회
            brand_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".sc.cs_convenience_store"))
            )
            event_type_tabs = brand_section.find_elements(By.CSS_SELECTOR, ".event_tab .tab")

            for i in range(len(event_type_tabs)):
                b_section = driver.find_element(By.CSS_SELECTOR, ".sc.cs_convenience_store")
                e_tab = b_section.find_elements(By.CSS_SELECTOR, ".event_tab .tab")[i]
                event_type = e_tab.text.strip()
                if not event_type or "전체" in event_type: continue

                print(f"    >> '{event_type}' 탭 클릭...")
                e_tab.click()
                time.sleep(1)

                product_list = b_section.find_element(By.CSS_SELECTOR, ".list_item.on")
                products = product_list.find_elements(By.CSS_SELECTOR, ".item")
                
                for product_element in products:
                    try:
                        name = product_element.find_element(By.CSS_SELECTOR, ".name").text
                        price_str = product_element.find_element(By.CSS_SELECTOR, ".price").text.replace('원', '').replace(',', '')
                        image_element = product_element.find_element(By.CSS_SELECTOR, ".thumb")
                        image_url = image_element.get_attribute('data-lazysrc') or image_element.get_attribute('src')
                        
                        if not name or not price_str: continue

                        products_data.append({
                            "brand": brand_name, "name": name, "price": int(price_str),
                            "image_url": image_url, "event_type": event_type,
                        })
                    except Exception: continue
    
    except Exception as e:
        print(f"[오류] 최종 크롤링 중 예외가 발생했습니다: {e}")
    
    finally:
        print("WebDriver를 종료합니다.")
        driver.quit()

    print(f"\n--- 네이버 크롤링 최종 완료: 총 {len(products_data)}개 수집 ---")
    return products_data