from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("PULDA_DB_PATH", "data/pulda.db")
    attachment_dir: str = os.getenv("PULDA_ATTACHMENT_DIR", "data/attachments")
    max_attachment_mb: int = int(os.getenv("PULDA_MAX_ATTACHMENT_MB", "20"))
    timezone: str = os.getenv("PULDA_TIMEZONE", "Asia/Seoul")
    host: str = os.getenv("PULDA_HOST", "0.0.0.0")
    port: int = int(os.getenv("PULDA_PORT", "8000"))
    auto_review: bool = _bool("AUTO_REVIEW", True)
    auto_sync_notion: bool = _bool("AUTO_SYNC_NOTION", False)
    auto_sync_github: bool = _bool("AUTO_SYNC_GITHUB", False)
    review_hour: int = int(os.getenv("REVIEW_HOUR", "22"))
    review_minute: int = int(os.getenv("REVIEW_MINUTE", "30"))
    notion_token: str = os.getenv("NOTION_TOKEN", "")
    notion_parent_page_id: str = os.getenv("NOTION_PARENT_PAGE_ID", "")
    notion_sync_page_id: str = os.getenv("NOTION_SYNC_PAGE_ID", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_repository: str = os.getenv("GITHUB_REPOSITORY", "")
    github_branch: str = os.getenv("GITHUB_BRANCH", "main")
    daily_activity_ingest_token: str = os.getenv("PULDA_DAILY_ACTIVITY_INGEST_TOKEN", "")

settings = Settings()
