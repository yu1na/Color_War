from pathlib import Path
import sys

try:
    import whisper
except Exception:
    whisper = None

class Transcriber:
    def __init__(self, base_dir: Path):
        self.scripts_dir = base_dir / "scripts"
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

    def transcribe(self, audio_path: Path, model_name: str = "small") -> tuple[Path, str]:
        video_id = audio_path.stem
        txt_path = self.scripts_dir / f"{video_id}.txt"

        if whisper is None:
            mock_text = (
                f"이 영상은 {video_id}에 대한 내용입니다.\n"
                "정부 정책에 대한 다양한 의견이 제시되고 있습니다.\n"
                "시장 경제와 복지 정책 사이의 균형에 대한 논의가 이루어지고 있습니다.\n"
            )
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(mock_text)
            return txt_path, mock_text

        model = whisper.load_model(model_name)
        result = model.transcribe(str(audio_path), language="ko", verbose=False, fp16=False)
        text = result.get("text", "").strip()
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        return txt_path, text