import sys
import os
import re
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build

# UTF-8 인코딩 설정 (Windows 콘솔에서 한글 출력)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass  # 이미 설정된 경우 무시
    os.environ['PYTHONIOENCODING'] = 'utf-8'


def load_environment() -> None:
    """프로젝트 루트(.env) 환경변수 불러오기 (절대경로 고정)"""
    from pathlib import Path
    import os
    from dotenv import load_dotenv
    # 프로젝트 루트 경로 고정 (main.py를 어디서 실행하든 루트 기준)
    root_env_path = Path(__file__).parent.parent.resolve() / ".env"
    if not root_env_path.exists():
        print(f"[오류] .env 파일이 프로젝트 루트에 없습니다: {root_env_path}")
        print("예시: YOUTUBE_DATA_API_KEY=your_api_key_here\n")
        return
    load_dotenv(str(root_env_path), override=True)


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    patterns = [
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'youtu\.be/([a-zA-Z0-9_-]+)',
        r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError("Invalid YouTube URL")


def safe_print(text: str) -> None:
    """Safely print text handling encoding issues."""
    try:
        print(text)
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        # Try to handle encoding issues
        try:
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='ignore')
            print(text.encode('ascii', errors='ignore').decode('ascii'))
        except:
            try:
                # Last resort: try to print as ASCII
                print(str(text).encode('ascii', errors='replace').decode('ascii'))
            except:
                print("(인코딩 오류로 텍스트를 표시할 수 없습니다)")


def extract_all_comments(youtube, video_id: str) -> List[str]:
    """Extract all comments and replies from a YouTube video."""
    all_comments = []
    
    try:
        # Top-level comments
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100
        )
        
        while request is not None:
            response = request.execute()
            
            for item in response['items']:
                # Top-level comment
                try:
                    comment_snippet = item['snippet']['topLevelComment']['snippet']
                    top_level_comment = comment_snippet.get('textDisplay', comment_snippet.get('textOriginal', ''))
                    # Clean comment text
                    if isinstance(top_level_comment, str):
                        all_comments.append(top_level_comment)
                except (KeyError, UnicodeDecodeError) as e:
                    pass
                
                # Replies
                if 'replies' in item:
                    for reply in item['replies']['comments']:
                        try:
                            reply_snippet = reply.get('snippet', {})
                            reply_text = reply_snippet.get('textDisplay', reply_snippet.get('textOriginal', ''))
                            # Clean reply text
                            if isinstance(reply_text, str):
                                all_comments.append(reply_text)
                        except (KeyError, UnicodeDecodeError):
                            pass
            
            # Get next page if available
            request = youtube.commentThreads().list_next(request, response)
            
    except Exception as e:
        try:
            error_msg = str(e)
            print(f"Error extracting comments: {error_msg}")
        except:
            print("Error extracting comments")
        return []
    
    return all_comments


def save_comments_to_file(comments: List[str], video_id: str, output_dir: Path) -> Path:
    """Save comments to a text file in the output directory."""
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename with video_id and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{video_id}_{timestamp}.txt"
    filepath = output_dir / filename
    
    # Write comments to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"YouTube Video ID: {video_id}\n")
            f.write(f"추출된 댓글 수: {len(comments)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, comment in enumerate(comments, 1):
                # Remove any HTML tags or special characters
                clean_comment = comment.replace('\r\n', ' ').replace('\n', ' ')
                f.write(f"[{i}] {clean_comment}\n\n")
        
        return filepath
    except Exception as e:
        print(f"Error saving comments to file: {e}")
        return None


def main() -> int:
    """Entry point for the application."""
    load_environment()
    
    api_key = os.getenv("YOUTUBE_DATA_API_KEY")
    
    if not api_key:
        print("YOUTUBE_DATA_API_KEY not found in .env file!")
        print("\n.env 파일이 프로젝트 루트에 있는지 확인하세요.")
        print("파일 내용 예시: YOUTUBE_DATA_API_KEY=your_api_key_here")
        return 1
    
    # Initialize YouTube API
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # Get YouTube URL from user
    print("=" * 60)
    print("YouTube 댓글 추출기")
    print("=" * 60)
    print()
    print("예시 URL 형식:")
    print("  - https://youtube.com/watch?v=VIDEO_ID")
    print("  - https://youtu.be/VIDEO_ID")
    print()
    url = input("YouTube URL을 입력하세요: ").strip()
    
    if not url:
        print("URL이 입력되지 않았습니다.")
        return 1
    
    try:
        # Extract video ID
        video_id = extract_video_id(url)
        print(f"\n비디오 ID: {video_id}")
        print("\n댓글을 추출하는 중...")
        
        # Extract all comments
        comments = extract_all_comments(youtube, video_id)
        
        if not comments:
            print("댓글을 찾을 수 없습니다.")
            return 0
        
        # Display results
        print("\n" + "=" * 60)
        safe_print(f"총 {len(comments)}개의 댓글을 찾았습니다.")
        print("=" * 60)
        print()
        
        # Save comments to file
        output_dir = Path(__file__).parent.parent / "extract_comments"
        saved_file = save_comments_to_file(comments, video_id, output_dir)
        
        if saved_file:
            print(f"\n댓글이 저장되었습니다:")
            print(f"  파일 위치: {saved_file}")
            print(f"  파일 크기: {os.path.getsize(saved_file)} bytes")
        else:
            print("\n댓글 저장 중 오류가 발생했습니다.")
        
        # Option to display comments on screen
        print("\n콘솔에 댓글을 표시할까요? (y/n): ", end="")
        try:
            show_comments = input().strip().lower()
            if show_comments == 'y' or show_comments == 'yes':
                print("\n" + "=" * 60)
                for i, comment in enumerate(comments, 1):
                    safe_print(f"[{i}] {comment}\n")
        except:
            pass
            
    except ValueError as e:
        print(f"오류: {e}")
        return 1
    except Exception as e:
        print(f"오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

