"""
API 테스트 스크립트
서버가 실행 중일 때 이 스크립트를 실행하여 전체 워크플로우를 테스트할 수 있습니다.
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def main():
    print_section("정치 댓글 전쟁 시뮬레이터 API 테스트")
    
    # 1. 헬스 체크
    print_section("1. 서버 상태 확인")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        health = response.json()
        print(f"✓ 서버 상태: {health['status']}")
        print(f"  - 모드: {health['mode']}")
        print(f"  - CUDA 사용 가능: {health['cuda_available']}")
        print(f"  - 디바이스: {health['device']}")
        print(f"  - 페르소나 준비: {health['persona_ready']}")
    except Exception as e:
        print(f"✗ 서버 연결 실패: {e}")
        print("서버가 실행 중인지 확인하세요: python backend/main.py")
        return
    
    # 2. 좌파 댓글 수집
    print_section("2. 좌파 댓글 수집")
    left_comments = [
        "진보적 개혁이 필요합니다",
        "복지 예산을 대폭 늘려야 해요",
        "평등한 사회를 만들어야 합니다",
        "인권을 최우선으로 생각해야 합니다",
        "환경 보호가 시급합니다",
        "노동자의 권리를 보장해야 합니다",
        "재벌 개혁이 필요합니다"
    ]
    
    response = requests.post(
        f"{BASE_URL}/api/comments/left",
        json={"comments": left_comments}
    )
    stats = response.json()
    print(f"✓ 좌파 댓글 {stats['left_count']}개 수집됨")
    
    # 3. 우파 댓글 수집
    print_section("3. 우파 댓글 수집")
    right_comments = [
        "경제 성장이 최우선입니다",
        "안보가 가장 중요합니다",
        "재정 건전성을 지켜야 합니다",
        "전통적 가치를 존중해야 합니다",
        "자유 시장 경제를 유지해야 합니다",
        "법과 질서가 중요합니다",
        "국가 안전이 우선입니다"
    ]
    
    response = requests.post(
        f"{BASE_URL}/api/comments/right",
        json={"comments": right_comments}
    )
    stats = response.json()
    print(f"✓ 우파 댓글 {stats['right_count']}개 수집됨")
    
    # 4. 통계 확인
    print_section("4. 수집 통계 확인")
    response = requests.get(f"{BASE_URL}/api/comments/stats")
    stats = response.json()
    print(f"총 댓글 수: {stats['total_count']}")
    print(f"  - 좌파: {stats['left_count']}개")
    print(f"  - 우파: {stats['right_count']}개")
    print(f"페르소나 준비 상태: {'✓ 준비됨' if stats['persona_ready'] else '✗ 더 필요함'}")
    
    if not stats['persona_ready']:
        print("\n⚠ 페르소나 학습을 위해 각 진영에 최소 5개의 댓글이 필요합니다.")
        return
    
    # 5. 댓글 분석
    print_section("5. 댓글 분석")
    sample_comments = """
    진보적 개혁이 필요합니다
    경제 성장이 우선이죠
    복지 예산을 늘려야 합니다
    재정 건전성을 지켜야 합니다
    평등한 사회를 만들어야 해요
    자유 시장이 중요합니다
    """
    
    print("분석 중... (로컬 LLM 사용, 시간이 걸릴 수 있습니다)")
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"comments_text": sample_comments}
    )
    
    if response.status_code == 200:
        analysis = response.json()
        print("✓ 분석 완료")
        print(f"  - 좌파 논점: {len(analysis['left_arguments'])}개")
        print(f"  - 우파 논점: {len(analysis['right_arguments'])}개")
        print(f"  - 논쟁 키워드: {len(analysis['controversial_keywords'])}개")
    else:
        print(f"✗ 분석 실패: {response.json()}")
        return
    
    # 6. 토론 시작
    print_section("6. 토론 시작")
    response = requests.post(f"{BASE_URL}/api/debate/start")
    debate = response.json()
    print(f"✓ 토론 시작됨")
    print(f"  - 초기 주제: {debate['state']['current_topic']}")
    
    # 7. 댓글 전쟁 시뮬레이션
    print_section("7. 댓글 전쟁 시뮬레이션 (10개)")
    print("AI들이 싸우는 중...\n")
    
    for i in range(10):
        response = requests.post(f"{BASE_URL}/api/debate/next")
        
        if response.status_code == 200:
            data = response.json()
            message = data['message']
            state = data['state']
            
            side_emoji = "🔵" if message['side'] == 'left' else "🔴"
            side_name = "좌파" if message['side'] == 'left' else "우파"
            
            print(f"{side_emoji} {side_name}: {message['content']}")
            print(f"   (주제: {state['current_topic']}, 메시지 #{state['message_count']})")
            print()
            
            # 응답 생성 시간 대기
            time.sleep(1)
        else:
            print(f"✗ 메시지 생성 실패: {response.json()}")
            break
    
    # 8. 최종 상태 확인
    print_section("8. 토론 최종 상태")
    response = requests.get(f"{BASE_URL}/api/debate/status")
    status = response.json()
    state = status['state']
    
    print(f"총 메시지 수: {state['message_count']}")
    print(f"현재 주제: {state['current_topic']}")
    print(f"다룬 주제들: {', '.join(state['topics_covered']) if state['topics_covered'] else '없음'}")
    print(f"토론 진행 중: {'예' if state['is_active'] else '아니오'}")
    
    print_section("테스트 완료!")
    print("더 많은 메시지를 생성하려면 POST /api/debate/next를 호출하세요.")
    print("초기화하려면 POST /api/debate/reset을 호출하세요.")


if __name__ == "__main__":
    main()

