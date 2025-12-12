#!/usr/bin/env python3
"""모듈 임포트 테스트"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
print(f"BASE_DIR: {BASE_DIR}\n")

# Test 1: Factcheck 모듈
print("="*60)
print("Test 1: Factcheck 모듈")
print("="*60)
try:
    factcheck_sys_path = str(BASE_DIR / "factcheck")
    if factcheck_sys_path not in sys.path:
        sys.path.insert(0, factcheck_sys_path)
    
    import importlib.util
    api_path = BASE_DIR / "factcheck" / "api.py"
    spec = importlib.util.spec_from_file_location("factcheck_api", api_path)
    factcheck_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factcheck_module)
    factcheck_app = factcheck_module.app
    print("✅ Factcheck 모듈 로드 성공!")
except Exception as e:
    print(f"❌ Factcheck 모듈 로드 실패: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Persona 모듈
print("\n" + "="*60)
print("Test 2: Persona 모듈")
print("="*60)
try:
    persona_sys_path = str(BASE_DIR / "persona")
    persona_backend_path = str(BASE_DIR / "persona" / "backend")
    if persona_sys_path not in sys.path:
        sys.path.insert(0, persona_sys_path)
    if persona_backend_path not in sys.path:
        sys.path.insert(0, persona_backend_path)
    
    from backend.routes import (
        comments_router,
        persona_router,
        debate_router,
        health_router as persona_health_router
    )
    print("✅ Persona 모듈 로드 성공!")
except Exception as e:
    print(f"❌ Persona 모듈 로드 실패: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Structure 모듈
print("\n" + "="*60)
print("Test 3: Structure 모듈")
print("="*60)
try:
    structure_sys_path = str(BASE_DIR / "structure")
    if structure_sys_path not in sys.path:
        sys.path.insert(0, structure_sys_path)
    
    from routes.youtube_routes import router as youtube_router
    from routes.topic_routes import router as topic_router
    print("✅ Structure 모듈 로드 성공!")
except Exception as e:
    print(f"❌ Structure 모듈 로드 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("테스트 완료!")
print("="*60)

