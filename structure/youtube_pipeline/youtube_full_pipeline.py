from pathlib import Path
import os
import sys

# 가볍게 모듈화된 컴포넌트들을 임포트
from .audio import AudioDownloader
from .transcribe import Transcriber
from .summarizer import Summarizer
from .comments import CommentCollector
from .analyzer import Analyzer
from .saver import ResultsSaver

class YouTubeFullPipeline:
    def __init__(self, base_dir: Path = None):
        # base_dir가 str로 전달될 수 있으므로 항상 Path로 변환
        if base_dir is None:
            self.base_dir = Path.cwd()
        else:
            self.base_dir = Path(base_dir)
        
        # structure/data/ 경로 설정
        # base_dir이 structure 폴더면 그 안의 data, 아니면 base_dir/data
        if self.base_dir.name == "structure":
            self.data_dir = self.base_dir / "data"
        elif (self.base_dir / "data").exists():
            self.data_dir = self.base_dir / "data"
        else:
            # base_dir이 이미 data 폴더이거나 다른 경로인 경우
            self.data_dir = self.base_dir if self.base_dir.name == "data" else self.base_dir / "data"
        
        # 모든 컴포넌트에 data_dir 전달
        self.audio = AudioDownloader(self.data_dir)
        self.transcriber = Transcriber(self.data_dir)
        self.summarizer = Summarizer(self.data_dir)
        self.collector = CommentCollector(self.data_dir)
        self.analyzer = Analyzer()
        self.saver = ResultsSaver(self.data_dir)

    def extract_video_id(self, url_or_id: str) -> str:
        import re
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
            return url_or_id
        from urllib.parse import urlparse, parse_qs
        p = urlparse(url_or_id)
        if p.netloc:
            q = parse_qs(p.query)
            return q.get("v", [""])[0]
        return ""

    def run_full_pipeline(self, youtube_url: str):
        print(f"[파이프라인 시작] URL: {youtube_url}")

        # 1) 비디오 ID
        vid = self.extract_video_id(youtube_url)
        print(f"📹 비디오 ID: {vid}")
        if not vid:
            print("❌ 유효하지 않은 비디오 ID")
            return {}
        
        # 2단계: 오디오 다운로드
        print("🎵 오디오 다운로드 중...")
        audio_path = self.audio.download(vid)
        print(f"🎵 오디오 경로: {audio_path}")
        
        # 3단계: 음성 전사
        print("🎤 음성 전사 중...")
        script_path, text = self.transcriber.transcribe(audio_path)
        print(f"📝 전사 완료, 텍스트 길이: {len(text)} 문자")
        
        # 4단계: 요약 생성
        print("📝 요약 생성 중...")
        structured = self.summarizer.build_structured_summary(text)
        summary_sentences = self.summarizer.extract_summary(text, max_sentences=3)
        self.summarizer.save_summary(vid, summary_sentences)
        keywords = self.summarizer.extract_keywords_from_summary(summary_sentences)
        print(f"📝 요약 완료, 키워드: {keywords}")
        
        # 5단계: 댓글 수집
        print("💬 댓글 수집 중...")
        comments = self.collector.collect_comments(vid)
        print(f"💬 수집된 댓글 수: {len(comments) if comments else 0}")
        if not comments:
            print("⚠️  댓글을 찾을 수 없습니다. 요약만 반환합니다.")
            # 댓글 없이도 기본 결과 반환
            return {
                'video_id': vid,
                'summary': {
                    'structured': structured,
                    'sentences': summary_sentences,
                    'keywords': keywords
                },
                'analysis': {
                    'statistics': {
                        'total': 0,
                        'left_count': 0,
                        'right_count': 0
                    },
                    'left_comments': [],
                    'right_comments': []
                },
                'debate': [],
                'message': '댓글 수집 실패 - 요약만 생성됨'
            }
        
        # 6단계: 댓글 분석
        print("🔍 댓글 분석 중...")
        analysis = self.analyzer.analyze_comments(comments, summary_sentences)
        saved_files = self.saver.save_leftright_comments(vid, analysis.get('comments', []))
        print(f"  통계: {analysis.get('statistics', {})}")

        # 7) 요약 문장을 1문장으로 재요약 (토론 주제용)
        print("\n📝 토론 주제 생성 중...")
        debate_topic_sentence = None
        
        try:
            import requests
            from openai import OpenAI
            import os
            
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key and summary_sentences:
                client = OpenAI(api_key=openai_api_key)
                summary_text = "\n".join(summary_sentences)
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "당신은 긴 요약문을 핵심 논쟁거리 한 문장으로 압축하는 전문가입니다."},
                        {"role": "user", "content": f"다음 요약 내용에서 가장 논쟁적이고 좌우가 싸울만한 핵심 주제를 단 1문장(20자 이내)으로 요약하세요:\n\n{summary_text}"}
                    ],
                    temperature=0.7,
                    max_tokens=50
                )
                
                debate_topic_sentence = response.choices[0].message.content.strip()
                print(f"   🎯 토론 주제: {debate_topic_sentence}")
            else:
                # OpenAI 없으면 첫 문장 사용
                debate_topic_sentence = summary_sentences[0] if summary_sentences else "정치 이슈"
                print(f"   🎯 토론 주제: {debate_topic_sentence} (요약 없이 첫 문장 사용)")
                
        except Exception as e:
            print(f"   ⚠️ 토론 주제 생성 실패: {e}")
            debate_topic_sentence = summary_sentences[0] if summary_sentences else "정치 이슈"
            print(f"   🎯 토론 주제: {debate_topic_sentence} (폴백)")
        
        # 8) Persona에 댓글 전달 (신뢰도 높은 순으로 5개씩 선택)
        print("\n📤 Persona 시스템에 댓글 전달 중...")
        
        # 신뢰도 기준으로 상위 5개 선택
        left_comments_data = [c for c in analysis.get('comments', []) 
                             if c.get('political_orientation') == '좌파']
        right_comments_data = [c for c in analysis.get('comments', []) 
                              if c.get('political_orientation') == '우파']
        
        # 신뢰도 높은 순으로 정렬
        left_comments_data.sort(key=lambda x: x.get('classification_confidence', 0), reverse=True)
        right_comments_data.sort(key=lambda x: x.get('classification_confidence', 0), reverse=True)
        
        # 상위 5개 선택
        left_comments = [c['text'] for c in left_comments_data[:5]]
        right_comments = [c['text'] for c in right_comments_data[:5]]
        
        print(f"   좌파 댓글: {len(left_comments)}개 (신뢰도 높은 순)")
        if left_comments_data[:5]:
            avg_conf = sum(c.get('classification_confidence', 0) for c in left_comments_data[:5]) / len(left_comments_data[:5])
            print(f"      평균 신뢰도: {avg_conf:.2f}")
        
        print(f"   우파 댓글: {len(right_comments)}개 (신뢰도 높은 순)")
        if right_comments_data[:5]:
            avg_conf = sum(c.get('classification_confidence', 0) for c in right_comments_data[:5]) / len(right_comments_data[:5])
            print(f"      평균 신뢰도: {avg_conf:.2f}")
        
        try:
            import requests
            # Persona API에 댓글 전달
            if left_comments:
                resp = requests.post("http://localhost:8000/api/persona/comments/left", 
                                   json={"comments": left_comments}, timeout=5)
                if resp.status_code == 200:
                    print("   ✅ 좌파 댓글 5개 전달 완료")
                else:
                    print(f"   ⚠️ 좌파 댓글 전달 실패: {resp.status_code}")
            
            if right_comments:
                resp = requests.post("http://localhost:8000/api/persona/comments/right", 
                                   json={"comments": right_comments}, timeout=5)
                if resp.status_code == 200:
                    print("   ✅ 우파 댓글 5개 전달 완료")
                else:
                    print(f"   ⚠️ 우파 댓글 전달 실패: {resp.status_code}")
            
            # Persona 생성 및 토론 시작
            if len(left_comments) >= 5 and len(right_comments) >= 5:
                print("\n🎭 Persona 생성 중...")
                resp = requests.post("http://localhost:8000/api/persona/persona/generate", timeout=30)
                if resp.status_code == 200:
                    print("   ✅ Persona 생성 완료")
                    
                    # 토론 시작 (1문장 토론 주제 전달)
                    if debate_topic_sentence:
                        print(f"\n⚔️ 토론 시작 (주제: {debate_topic_sentence})")
                        debate_resp = requests.post(
                            "http://localhost:8000/api/persona/debate/start",
                            json={"summary_sentences": [debate_topic_sentence]},  # 1문장만 전달
                            timeout=10
                        )
                        if debate_resp.status_code == 200:
                            print("   ✅ 토론 세션 시작 완료")
                        else:
                            print(f"   ⚠️ 토론 시작 실패: {debate_resp.status_code}")
                else:
                    print(f"   ⚠️ Persona 생성 실패: {resp.status_code}")
            else:
                print(f"   ⚠️ Persona 생성 스킵 (좌:{len(left_comments)}, 우:{len(right_comments)}, 각 5개 필요)")
                
        except requests.exceptions.ConnectionError:
            print("   ⚠️ Persona 서버에 연결할 수 없습니다 (http://localhost:8000)")
        except Exception as e:
            print(f"   ⚠️ Persona 전달 중 오류: {e}")

        # 8) 결과 저장
        debate = []  # 토론 비활성화
        self.saver.save_results(vid, structured, analysis, debate, keywords)
        print("\n✅ 파이프라인 완료!")
        print("요약:", summary_sentences)
        return {'video_id': vid, 'summary': structured, 'analysis': analysis, 'debate': debate, 'summary_sentences': summary_sentences,}

# 간단 실행용 스크립트 유지
def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    url = "https://www.youtube.com/watch?v=QES-uZV3-gw"
    p = YouTubeFullPipeline(Path(__file__).parent)
    res = p.run_full_pipeline(url)
    print("완료:", bool(res))

if __name__ == "__main__":
    main()