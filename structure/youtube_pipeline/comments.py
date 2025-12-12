from pathlib import Path
import os
import json
from typing import List
from googleapiclient.discovery import build as _maybe_import_build  # optional import hint; handled at runtime
from dotenv import load_dotenv

# .env 파일 로드 (env 폴더에서)
load_dotenv(dotenv_path=Path(__file__).parent.parent / "env" / ".env")

class CommentCollector:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.comments_dir = base_dir / "comments"
        self.comments_dir.mkdir(parents=True, exist_ok=True)

    def collect_comments(self, video_id: str) -> List[str]:
        # 직접 API 키 설정 (임시)
        api_key = os.getenv('YOUTUBE_API_KEY') or "AIzaSyB1s4wsQDCKf5GaMWfk81xahB8c8aw0D04"
        print(f"🔑 YouTube API 키 확인: {'설정됨' if api_key else '없음'}")
        
        if not api_key:
            print("❌ YouTube API 키가 설정되지 않았습니다")
            return []
        
        try:
            from googleapiclient.discovery import build
            youtube = build('youtube', 'v3', developerKey=api_key)
            print(f"🔑 YouTube API 연결 성공")
            
            all_comments = self.extract_all_comments(youtube, video_id)
            print(f"💬 API로 수집된 댓글: {len(all_comments)}개")
            
            filtered = [c for c in all_comments if len(c) > 10]
            print(f"💬 필터링된 댓글: {len(filtered)}개")
            
            self.save_comments(video_id, filtered)
            return filtered
        except Exception as e:
            print(f"❌ YouTube API 오류: {e}")
            return []

    def extract_all_comments(self, youtube, video_id: str) -> List[str]:
        all_comments = []
        try:
            print(f"🔍 댓글 요청 시작: video_id={video_id}")
            request = youtube.commentThreads().list(part="snippet,replies", videoId=video_id, maxResults=100)
            page_count = 0
            while request is not None:
                response = request.execute()
                page_count += 1
                items = response.get('items', [])
                print(f"📄 페이지 {page_count}: {len(items)}개 스레드")
                
                for item in items:
                    try:
                        top = item['snippet']['topLevelComment']['snippet']
                        text = top.get('textDisplay', top.get('textOriginal',''))
                        if isinstance(text, str): all_comments.append(text)
                    except Exception as e:
                        print(f"⚠️  최상위 댓글 파싱 실패: {e}")
                        pass
                    for r in item.get('replies', {}).get('comments', []):
                        try:
                            rt = r.get('snippet', {}).get('textDisplay', '')
                            if isinstance(rt, str): all_comments.append(rt)
                        except Exception as e:
                            print(f"⚠️  답글 파싱 실패: {e}")
                            pass
                request = youtube.commentThreads().list_next(request, response)
            
            print(f"✅ 총 {len(all_comments)}개 댓글 수집 완료")
        except Exception as e:
            print(f"❌ 댓글 수집 중 오류: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []
        return all_comments


    def save_comments(self, video_id: str, comments: List[str]):
        fpath = self.comments_dir / f"{video_id}_comments.txt"
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(f"YouTube 댓글: {video_id}\n")
            f.write("="*50 + "\n\n")
            for i, c in enumerate(comments,1):
                f.write(f"{i}. {c}\n")
        return fpath