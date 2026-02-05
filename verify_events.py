import json
from collections import Counter

try:
    with open('gs25_products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    event_types = [item.get('event_type') for item in data]
    counts = Counter(event_types)

    print("\n'gs25_products.json' 파일의 행사 종류별 상품 개수:")
    if not counts:
        print("  - 분석할 데이터가 없습니다.")
    else:
        for event, count in counts.items():
            print(f"- {event}: {count}개")

except FileNotFoundError:
    print("오류: 'gs25_products.json' 파일을 찾을 수 없습니다.")
except json.JSONDecodeError:
    print("오류: 'gs25_products.json' 파일이 올바른 JSON 형식이 아닙니다.")
