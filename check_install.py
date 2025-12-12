#!/usr/bin/env python3
"""
ColorWar 설치 확인 스크립트
"""
import sys
import subprocess

def check_command(cmd, name):
    """외부 명령어 확인"""
    try:
        result = subprocess.run([cmd, '--version'], 
                                capture_output=True, 
                                text=True, 
                                timeout=5)
        if result.returncode == 0:
            print(f"✅ {name}: 설치됨")
            return True
        else:
            print(f"❌ {name}: 미설치")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"❌ {name}: 미설치")
        return False

def check_module(module_name, import_name=None):
    """Python 모듈 확인"""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        print(f"✅ {module_name}: 설치됨")
        return True
    except ImportError:
        print(f"❌ {module_name}: 미설치")
        return False

def main():
    print("="*60)
    print("ColorWar 설치 확인")
    print("="*60)
    print()
    
    print("📦 외부 프로그램:")
    ffmpeg_ok = check_command('ffmpeg', 'ffmpeg')
    print()
    
    print("📦 Python 패키지:")
    fastapi_ok = check_module('fastapi')
    uvicorn_ok = check_module('uvicorn')
    torch_ok = check_module('torch')
    transformers_ok = check_module('transformers')
    pydantic_ok = check_module('pydantic')
    pydantic_settings_ok = check_module('pydantic-settings', 'pydantic_settings')
    sentence_transformers_ok = check_module('sentence-transformers', 'sentence_transformers')
    whisper_ok = check_module('openai-whisper', 'whisper')
    print()
    
    print("="*60)
    all_ok = (
        ffmpeg_ok and 
        fastapi_ok and 
        uvicorn_ok and 
        torch_ok and 
        transformers_ok and 
        pydantic_ok and 
        pydantic_settings_ok and 
        sentence_transformers_ok and 
        whisper_ok
    )
    
    if all_ok:
        print("✅ 모든 의존성이 설치되었습니다!")
        print("🚀 서버 실행: python RunColorWar.py")
    else:
        print("❌ 일부 의존성이 누락되었습니다.")
        print()
        if not ffmpeg_ok:
            print("📌 ffmpeg 설치:")
            print("   macOS: brew install ffmpeg")
            print("   Linux: sudo apt install ffmpeg")
        if not all([pydantic_settings_ok, fastapi_ok, uvicorn_ok, torch_ok]):
            print("📌 Python 패키지 설치:")
            print("   pip install -r require.txt")
    print("="*60)

if __name__ == "__main__":
    main()

