"""
API 테스트 스크립트

사용법:
    # 서버가 실행 중인 상태에서
    python3 test_api.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """헬스체크 테스트"""
    print("\n" + "="*80)
    print("📡 헬스체크")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_single_factcheck(claim: str):
    """단일 팩트체크 테스트"""
    print("\n" + "="*80)
    print(f"🔍 팩트체크: {claim}")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/factcheck",
        json={"claim": claim}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 판정: {result['verdict']}")
        print(f"⭐ 신뢰도: {result['confidence_score']}/10 ({result['confidence_level']})")
        print(f"💡 근거: {result['reasoning']}")
        print(f"📚 Evidence: {len(result['evidences'])}개")
    else:
        print(f"❌ 에러: {response.json()}")


def test_batch_factcheck():
    """배치 팩트체크 테스트"""
    print("\n" + "="*80)
    print("📦 배치 팩트체크")
    print("="*80)
    
    claims = [
        "M5맥북 출시 임박",
        "한강에 괴물 출현",
        "마을버스 요금인상"
    ]
    
    response = requests.post(
        f"{BASE_URL}/factcheck/batch",
        json={"claims": claims}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n총 {result['total']}개 처리:")
        
        for idx, res in enumerate(result['results'], 1):
            print(f"\n[{idx}] {res['claim']}")
            print(f"    판정: {res['verdict']} ({res['confidence_score']}/10)")
    else:
        print(f"❌ 에러: {response.json()}")


if __name__ == "__main__":
    try:
        print("🚀 팩트체크 API 테스트 시작")
        print(f"📡 서버 주소: {BASE_URL}")
        
        # 1. 헬스체크
        test_health()
        
        # 2. 단일 팩트체크
        test_single_factcheck("M5맥북 출시 임박")
        test_single_factcheck("한강에 괴물 출현")
        
        # 3. 배치 팩트체크
        test_batch_factcheck()
        
        print("\n" + "="*80)
        print("✅ 모든 테스트 완료!")
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 에러: 서버에 연결할 수 없습니다.")
        print("💡 먼저 서버를 시작하세요:")
        print("   uvicorn api:app --reload --host 0.0.0.0 --port 8000")
    
    except Exception as e:
        print(f"\n❌ 에러: {e}")

