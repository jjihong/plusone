import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from crawlers.all_crawler import crawl_all

def main():
    """
    통합 크롤러를 실행하여 모든 편의점의 행사 상품을 수집하고,
    결과를 JSON 파일 및 Supabase 데이터베이스에 저장합니다.
    """
    print("통합 편의점 행사 상품 크롤링을 시작합니다.")
    
    # 크롤링 실행
    all_products = crawl_all()

    if all_products:
        # 1. JSON 파일로 저장
        with open('all_products.json', 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=4)
        print(f"\n파일 저장 완료. 총 {len(all_products)}개의 상품 정보를 'all_products.json'에 저장했습니다.")

        # 2. Supabase에 데이터 삽입
        load_dotenv()
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            print("\n경고: Supabase 환경 변수가 설정되지 않아 데이터베이스에 업로드하지 않습니다.")
        else:
            try:
                supabase: Client = create_client(supabase_url, supabase_key)
                print("\nSupabase에 데이터 삽입을 시작합니다...")
                
                # 안정성을 위해 기존 데이터를 모두 지우고 새로 삽입합니다.
                print("기존 'products' 테이블의 데이터를 삭제합니다...")
                supabase.table('products').delete().neq('id', -1).execute() # 모든 행 삭제

                print("새로운 데이터를 삽입합니다...")
                response = supabase.table('products').insert(all_products).execute()
                
                if len(response.data) > 0:
                    print(f"Supabase에 총 {len(response.data)}개의 데이터가 성공적으로 삽입되었습니다.")
                else:
                    print("Supabase에 데이터 삽입 중 문제가 발생했을 수 있습니다.")
            except Exception as e:
                print(f"Supabase 작업 중 오류 발생: {e}")
    else:
        print("\n수집된 상품이 없습니다.")

    print("\n모든 크롤링 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()
