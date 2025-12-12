"""
API 테스트 스크립트
서버가 실행 중일 때 이 스크립트를 실행하여 전체 워크플로우를 테스트할 수 있습니다.

사용법:
    python test_api.py              # 기본 테스트 (10개 메시지)
    python test_api.py --messages 20  # 20개 메시지 생성
    python test_api.py --quick       # 빠른 테스트 (페르소나만)
"""
import requests
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

# ANSI 색상 코드
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def main(num_messages=10, quick_test=False):
    print_section("🧠 정치 댓글 전쟁 시뮬레이터 API 테스트")
    print(f"{Colors.BOLD}시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")
    
    # 1. 헬스 체크
    print_section("1️⃣ 서버 상태 확인")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        health = response.json()
        print_success(f"서버 상태: {health['status']}")
        print(f"  {Colors.BOLD}CUDA 사용 가능:{Colors.END} {health['cuda_available']}")
        print(f"  {Colors.BOLD}디바이스:{Colors.END} {health['device']}")
        
        stats = health.get('persona_stats', {})
        print(f"  {Colors.BOLD}좌파 댓글:{Colors.END} {stats.get('left_count', 0)}개")
        print(f"  {Colors.BOLD}우파 댓글:{Colors.END} {stats.get('right_count', 0)}개")
        print(f"  {Colors.BOLD}페르소나 생성 여부:{Colors.END} {stats.get('personas_generated', False)}")
    except Exception as e:
        print_error(f"서버 연결 실패: {e}")
        print_info("서버가 실행 중인지 확인하세요: cd persona/backend && python main.py")
        return
    
    # 2. 좌파 댓글 수집
    print_section("2️⃣ 좌파 댓글 수집")
    left_comments = [
        "진보적 개혁이 필요합니다",
        "복지 예산을 대폭 늘려야 해요",
        "평등한 사회를 만들어야 합니다",
        "인권을 최우선으로 생각해야 합니다",
        "환경 보호가 시급합니다",
        "노동자의 권리를 보장해야 합니다",
        "재벌 개혁이 필요합니다"
    ]
    
    print_info(f"{len(left_comments)}개의 댓글 전송 중...")
    for i, comment in enumerate(left_comments[:3], 1):
        print(f"  {Colors.BLUE}└─{Colors.END} {comment}")
    if len(left_comments) > 3:
        print(f"  {Colors.BLUE}└─{Colors.END} ... 외 {len(left_comments)-3}개")
    
    response = requests.post(
        f"{BASE_URL}/api/comments/left",
        json={"comments": left_comments}
    )
    stats = response.json()
    print_success(f"좌파 댓글 {stats['left_count']}개 수집 완료")
    
    # 3. 우파 댓글 수집
    print_section("3️⃣ 우파 댓글 수집")
    right_comments = [
        "경제 성장이 최우선입니다",
        "안보가 가장 중요합니다",
        "재정 건전성을 지켜야 합니다",
        "전통적 가치를 존중해야 합니다",
        "자유 시장 경제를 유지해야 합니다",
        "법과 질서가 중요합니다",
        "국가 안전이 우선입니다"
    ]
    
    print_info(f"{len(right_comments)}개의 댓글 전송 중...")
    for i, comment in enumerate(right_comments[:3], 1):
        print(f"  {Colors.RED}└─{Colors.END} {comment}")
    if len(right_comments) > 3:
        print(f"  {Colors.RED}└─{Colors.END} ... 외 {len(right_comments)-3}개")
    
    response = requests.post(
        f"{BASE_URL}/api/comments/right",
        json={"comments": right_comments}
    )
    stats = response.json()
    print_success(f"우파 댓글 {stats['right_count']}개 수집 완료")
    
    # 4. 통계 확인
    print_section("4️⃣ 수집 통계 확인")
    response = requests.get(f"{BASE_URL}/api/comments/stats")
    stats = response.json()
    print(f"{Colors.BOLD}총 댓글 수:{Colors.END} {stats['left_count'] + stats['right_count']}개")
    print(f"  {Colors.BLUE}└─ 좌파:{Colors.END} {stats['left_count']}개")
    print(f"  {Colors.RED}└─ 우파:{Colors.END} {stats['right_count']}개")
    print(f"{Colors.BOLD}페르소나 준비:{Colors.END} {'✓ 준비됨' if stats['persona_ready'] else '✗ 더 필요함'}")
    
    if not stats['persona_ready']:
        print_warning("페르소나 학습을 위해 각 진영에 최소 5개의 댓글이 필요합니다.")
        return
    
    # 5. 페르소나 생성
    print_section("5️⃣ LLM 기반 페르소나 생성")
    print_info("수집된 댓글을 분석하여 페르소나 생성 중...")
    print_warning("LLM 처리 시간이 소요될 수 있습니다 (1-2분)")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/comments/generate-persona")
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print_success(f"페르소나 생성 완료 (소요 시간: {elapsed:.1f}초)")
        
        left_p = result.get('left_persona', {})
        right_p = result.get('right_persona', {})
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}📋 좌파 페르소나:{Colors.END}")
        print(f"  {Colors.BOLD}요약:{Colors.END} {left_p.get('summary', 'N/A')}")
        print(f"  {Colors.BOLD}가치관:{Colors.END} {', '.join(left_p.get('values', []))}")
        print(f"  {Colors.BOLD}말투:{Colors.END} {', '.join(left_p.get('tone', []))}")
        print(f"  {Colors.BOLD}감정:{Colors.END} {left_p.get('emotion', 'N/A')}")
        
        print(f"\n{Colors.BOLD}{Colors.RED}📋 우파 페르소나:{Colors.END}")
        print(f"  {Colors.BOLD}요약:{Colors.END} {right_p.get('summary', 'N/A')}")
        print(f"  {Colors.BOLD}가치관:{Colors.END} {', '.join(right_p.get('values', []))}")
        print(f"  {Colors.BOLD}말투:{Colors.END} {', '.join(right_p.get('tone', []))}")
        print(f"  {Colors.BOLD}감정:{Colors.END} {right_p.get('emotion', 'N/A')}")
    else:
        print_error(f"페르소나 생성 실패: {response.json()}")
        return
    
    if quick_test:
        print_section("✅ 빠른 테스트 완료!")
        print_info("전체 토론 테스트를 실행하려면: python test_api.py")
        return
    
    # 6. 토론 시작
    print_section("6️⃣ AI 토론 시작")
    response = requests.post(f"{BASE_URL}/api/debate/start")
    debate = response.json()
    print_success("토론 세션 시작")
    print(f"  {Colors.BOLD}초기 주제:{Colors.END} {debate['state']['current_topic']}")
    
    # 7. 댓글 전쟁 시뮬레이션
    print_section(f"7️⃣ 댓글 전쟁 시뮬레이션 ({num_messages}개 메시지)")
    print_info("AI들이 실시간으로 논쟁 중입니다...\n")
    
    for i in range(num_messages):
        print(f"{Colors.BOLD}[{i+1}/{num_messages}]{Colors.END} 메시지 생성 중...")
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/debate/next")
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            message = data['message']
            state = data['state']
            
            if message['side'] == 'left':
                side_color = Colors.BLUE
                side_emoji = "🔵"
                side_name = "좌파"
            else:
                side_color = Colors.RED
                side_emoji = "🔴"
                side_name = "우파"
            
            print(f"\n{side_color}{Colors.BOLD}{side_emoji} {side_name}:{Colors.END}")
            print(f"{side_color}{message['content']}{Colors.END}")
            print(f"{Colors.CYAN}└─ 주제: {state['current_topic']} | 메시지 #{state['message_count']} | 생성시간: {elapsed:.1f}초{Colors.END}")
            
            # 다음 메시지까지 약간의 딜레이
            time.sleep(0.5)
        else:
            print_error(f"메시지 생성 실패: {response.json()}")
            break
    
    # 8. 최종 상태 확인
    print_section("8️⃣ 토론 최종 상태")
    response = requests.get(f"{BASE_URL}/api/debate/status")
    status = response.json()
    state = status['state']
    
    print(f"{Colors.BOLD}총 메시지 수:{Colors.END} {state['message_count']}")
    print(f"{Colors.BOLD}현재 주제:{Colors.END} {state['current_topic']}")
    print(f"{Colors.BOLD}다룬 주제들:{Colors.END} {', '.join(state['topics_covered']) if state['topics_covered'] else '없음'}")
    print(f"{Colors.BOLD}토론 진행 중:{Colors.END} {'예' if state['is_active'] else '아니오'}")
    
    print_section("✅ 테스트 완료!")
    print(f"{Colors.BOLD}종료 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")
    print_info("추가 옵션:")
    print(f"  {Colors.CYAN}└─{Colors.END} 더 많은 메시지: POST /api/debate/next")
    print(f"  {Colors.CYAN}└─{Colors.END} 토론 초기화: POST /api/debate/reset")
    print(f"  {Colors.CYAN}└─{Colors.END} 댓글 초기화: POST /api/comments/reset")


if __name__ == "__main__":
    # 명령줄 인자 파싱
    num_messages = 10
    quick_test = False
    
    if len(sys.argv) > 1:
        if "--quick" in sys.argv:
            quick_test = True
        if "--messages" in sys.argv:
            try:
                idx = sys.argv.index("--messages")
                num_messages = int(sys.argv[idx + 1])
            except (ValueError, IndexError):
                print_error("--messages 옵션에는 숫자를 입력해주세요")
                print_info("사용법: python test_api.py --messages 20")
                sys.exit(1)
        if "--help" in sys.argv or "-h" in sys.argv:
            print("""
정치 댓글 전쟁 시뮬레이터 - API 테스트 스크립트

사용법:
    python test_api.py                  # 기본 테스트 (10개 메시지)
    python test_api.py --messages 20    # 20개 메시지 생성
    python test_api.py --quick          # 빠른 테스트 (페르소나만)
    python test_api.py --help           # 도움말 표시

옵션:
    --messages N    생성할 메시지 개수 (기본: 10)
    --quick         빠른 테스트 모드 (페르소나 생성까지만)
    --help, -h      도움말 표시
            """)
            sys.exit(0)
    
    try:
        main(num_messages=num_messages, quick_test=quick_test)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}사용자에 의해 테스트가 중단되었습니다.{Colors.END}")
    except Exception as e:
        print_error(f"예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()

