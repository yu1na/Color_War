from pathlib import Path
from typing import List, Dict, Any

class ResultsSaver:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.comments_leftright_dir = base_dir / "comments_leftright"
        self.results_dir = base_dir / "results"
        self.comments_leftright_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def save_leftright_comments(self, video_id: str, reclassified_comments: List[Dict]) -> Dict[str, Path]:
        left = [c for c in reclassified_comments if c.get('political_orientation')=='좌파']
        right = [c for c in reclassified_comments if c.get('political_orientation')=='우파']
        files = {}
        if left:
            p = self.comments_leftright_dir / f"{video_id}_left.txt"
            with open(p, "w", encoding="utf-8") as f:
                f.write(f"YouTube 좌파 댓글: {video_id}\n\n")
                for i,c in enumerate(left,1):
                    f.write(f"{i}. {c['text']}\n  신뢰도: {c.get('classification_confidence',0):.2f}\n\n")
            files['left'] = p
        if right:
            p = self.comments_leftright_dir / f"{video_id}_right.txt"
            with open(p, "w", encoding="utf-8") as f:
                f.write(f"YouTube 우파 댓글: {video_id}\n\n")
                for i,c in enumerate(right,1):
                    f.write(f"{i}. {c['text']}\n  신뢰도: {c.get('classification_confidence',0):.2f}\n\n")
            files['right'] = p
        # summary file
        summary_p = self.comments_leftright_dir / f"{video_id}_classification_summary.txt"
        with open(summary_p, "w", encoding="utf-8") as f:
            f.write(f"YouTube 댓글 좌우 분류 결과: {video_id}\n\n")
            f.write(f"총 댓글 수: {len(reclassified_comments)}\n")
            f.write(f"좌파: {len(left)}개\n우파: {len(right)}개\n")
        files['summary'] = summary_p
        return files

    def save_results(self, video_id: str, summary: Dict[str,str], analysis: Dict[str,Any], debate: List[Dict], keywords: List[str] | None = None):
        p = self.results_dir / f"{video_id}_summary.txt"
        with open(p, "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write(f"YouTube 영상 분석 결과: {video_id}\n")
            f.write("="*60 + "\n\n")
            f.write("[요약]\n")
            f.write(f"개요: {summary.get('overview','')}\n핵심 발언: {summary.get('sayings','')}\n\n")
            if keywords:
                f.write("[키워드]\n" + ", ".join(keywords) + "\n\n")
            f.write("[댓글 분석]\n")
            for k,v in analysis.get('statistics',{}).items():
                f.write(f"- {k}: {v['count']}개 ({v['percentage']}%)\n")
            f.write("\n[토론]\n")
            for m in debate:
                f.write(f"{m['speaker']}: {m['message']}\n")
        return p