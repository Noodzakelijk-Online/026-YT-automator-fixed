"""Initial production schema.

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    op.create_table("user", sa.Column("id", sa.String(36), primary_key=True), sa.Column("email", sa.String(255), unique=True),
                    sa.Column("display_name", sa.String(255)), *timestamps())
    op.create_table("you_tube_account", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("channel_id", sa.String(128), nullable=False, unique=True), sa.Column("channel_title", sa.String(255), nullable=False),
        sa.Column("thumbnail_url", sa.Text), sa.Column("token_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("token_expiry", sa.DateTime(timezone=True)), sa.Column("scopes_json", sa.Text, nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)), *timestamps())
    op.create_index("ix_you_tube_account_user_id", "you_tube_account", ["user_id"])
    op.create_table("video_draft", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id"), nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False), sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("file_size", sa.BigInteger, nullable=False), sa.Column("mime_type", sa.String(100)),
        sa.Column("checksum", sa.String(64), nullable=False), sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=False), sa.Column("tags_json", sa.Text, nullable=False),
        sa.Column("hashtags_json", sa.Text, nullable=False), sa.Column("seo_keywords_json", sa.Text, nullable=False),
        sa.Column("category_id", sa.String(16), nullable=False), sa.Column("playlist_id", sa.String(128)),
        sa.Column("privacy_status", sa.String(16), nullable=False), sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_source", sa.String(16), nullable=False), sa.Column("manually_edited", sa.Boolean, nullable=False),
        sa.Column("youtube_video_id", sa.String(64), unique=True), sa.Column("youtube_url", sa.Text),
        sa.Column("upload_response_json", sa.Text), *timestamps())
    for name in ("user_id", "status", "checksum"): op.create_index(f"ix_video_draft_{name}", "video_draft", [name])
    op.create_table("transcript", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("draft_id", sa.String(36), sa.ForeignKey("video_draft.id"), nullable=False, unique=True),
        sa.Column("text", sa.Text, nullable=False), sa.Column("language", sa.String(16), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error", sa.Text), *timestamps())
    op.create_table("thumbnail", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("draft_id", sa.String(36), sa.ForeignKey("video_draft.id"), nullable=False),
        sa.Column("file_path", sa.Text, nullable=False), sa.Column("source", sa.String(32), nullable=False),
        sa.Column("selected", sa.Boolean, nullable=False), sa.Column("upload_status", sa.String(32), nullable=False),
        sa.Column("error", sa.Text), *timestamps())
    op.create_index("ix_thumbnail_draft_id", "thumbnail", ["draft_id"])
    op.create_table("playlist", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("you_tube_account.id"), nullable=False),
        sa.Column("youtube_playlist_id", sa.String(128), nullable=False), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("privacy_status", sa.String(16), nullable=False), *timestamps())
    op.create_table("batch_job", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False), sa.Column("total_count", sa.Integer, nullable=False), *timestamps())
    op.create_table("upload_job", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("draft_id", sa.String(36), sa.ForeignKey("video_draft.id"), nullable=False),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("batch_job.id")), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False), sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("worker_id", sa.String(128)), sa.Column("progress", sa.Integer, nullable=False),
        sa.Column("retry_count", sa.Integer, nullable=False), sa.Column("max_retries", sa.Integer, nullable=False),
        sa.Column("last_error", sa.Text), sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)), *timestamps())
    for name in ("draft_id", "status", "run_at"): op.create_index(f"ix_upload_job_{name}", "upload_job", [name])
    op.create_table("job_log", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("upload_job.id"), nullable=False),
        sa.Column("level", sa.String(16), nullable=False), sa.Column("event", sa.String(64), nullable=False),
        sa.Column("message", sa.Text, nullable=False), sa.Column("details_json", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_job_log_job_id", "job_log", ["job_id"])
    op.create_table("error_log", sa.Column("id", sa.Integer, primary_key=True), sa.Column("request_id", sa.String(36)),
        sa.Column("code", sa.String(64), nullable=False), sa.Column("message", sa.Text, nullable=False),
        sa.Column("details_json", sa.Text), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_error_log_request_id", "error_log", ["request_id"])


def downgrade():
    for table in ("error_log", "job_log", "upload_job", "batch_job", "playlist", "thumbnail", "transcript", "video_draft", "you_tube_account", "user"):
        op.drop_table(table)
