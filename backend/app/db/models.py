import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Text, Float, DateTime, ForeignKey, 
    UniqueConstraint, Index, JSON, Boolean, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan", order_by="Scene.scene_number")
    entities = relationship("Entity", back_populates="project", cascade="all, delete-orphan")
    facts = relationship("Fact", back_populates="project", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="project", cascade="all, delete-orphan")
    knowledge_states = relationship("KnowledgeState", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")
    issue_reviews = relationship("IssueReview", back_populates="project", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="project", cascade="all, delete-orphan")
    research_tasks = relationship("ResearchTask", back_populates="project", cascade="all, delete-orphan")
    plot_events = relationship("PlotEvent", back_populates="project", cascade="all, delete-orphan", order_by="PlotEvent.scene_number")
    settings = relationship("ProjectSettings", uselist=False, back_populates="project", cascade="all, delete-orphan")
    world_rules = relationship("StoryWorldRule", back_populates="project", cascade="all, delete-orphan", order_by="StoryWorldRule.created_at")
    imported_documents = relationship("ImportedDocument", back_populates="project", cascade="all, delete-orphan", order_by="ImportedDocument.created_at.desc()")


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    
    # Provenance fields
    source_document_id = Column(String(36), ForeignKey("imported_documents.id", ondelete="SET NULL"), nullable=True)
    source_page_start = Column(Integer, nullable=True)
    source_page_end = Column(Integer, nullable=True)
    source_type = Column(String(50), default="MANUAL", nullable=False)
    is_analyzed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "scene_number", name="uq_project_scene_number"),
        Index("ix_scenes_source_document_id", "source_document_id"),
    )

    # Relationships
    project = relationship("Project", back_populates="scenes")
    source_document = relationship("ImportedDocument", back_populates="scenes")
    events = relationship("Event", back_populates="scene", cascade="all, delete-orphan")
    facts = relationship("Fact", back_populates="scene", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="scene", cascade="all, delete-orphan")
    knowledge_states = relationship("KnowledgeState", back_populates="source_scene", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="scene", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="scene", cascade="all, delete-orphan")
    research_tasks = relationship("ResearchTask", back_populates="scene", cascade="all, delete-orphan")


class ImportedDocument(Base):
    __tablename__ = "imported_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=False)
    status = Column(String(50), default="UPLOADED", nullable=False)  # UPLOADED, PARSING, READY_FOR_REVIEW, IMPORTED, FAILED
    parser_version = Column(String(50), default="1.0.0", nullable=False)
    scene_detection_version = Column(String(50), default="1.0.0", nullable=False)
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    scene_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_imported_documents_project_id", "project_id"),
    )

    # Relationships
    project = relationship("Project", back_populates="imported_documents")
    scenes = relationship("Scene", back_populates="source_document")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # character | location | object | organization
    name = Column(String(255), nullable=False)
    attributes_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_entity_project_type_name", "project_id", "type", "name"),
    )

    # Relationships
    project = relationship("Project", back_populates="entities")
    facts = relationship("Fact", back_populates="subject_entity", cascade="all, delete-orphan")
    relationships_source = relationship("Relationship", foreign_keys="Relationship.source_entity_id", back_populates="source_entity", cascade="all, delete-orphan")
    relationships_target = relationship("Relationship", foreign_keys="Relationship.target_entity_id", back_populates="target_entity", cascade="all, delete-orphan")
    knowledge_states = relationship("KnowledgeState", back_populates="character_entity", cascade="all, delete-orphan")


class Fact(Base):
    __tablename__ = "facts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    subject_entity_id = Column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    predicate = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    source_type = Column(String(50), default="SCREENPLAY", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="facts")
    scene = relationship("Scene", back_populates="facts")
    subject_entity = relationship("Entity", back_populates="facts")


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    actor_entity_id = Column(String(36), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    target_entity_id = Column(String(36), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    location_entity_id = Column(String(36), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=False)
    attributes_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    scene = relationship("Scene", back_populates="events")
    actor_entity = relationship("Entity", foreign_keys=[actor_entity_id])
    target_entity = relationship("Entity", foreign_keys=[target_entity_id])
    location_entity = relationship("Entity", foreign_keys=[location_entity_id])


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    source_entity_id = Column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    target_entity_id = Column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=True)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    source_type = Column(String(50), default="SCREENPLAY", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="relationships")
    scene = relationship("Scene", back_populates="relationships")
    source_entity = relationship("Entity", foreign_keys=[source_entity_id], back_populates="relationships_source")
    target_entity = relationship("Entity", foreign_keys=[target_entity_id], back_populates="relationships_target")


class KnowledgeState(Base):
    __tablename__ = "knowledge_states"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    character_entity_id = Column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    knowledge = Column(Text, nullable=False)
    source_scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    knowledge_type = Column(String(50), default="explicitly_established", nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="knowledge_states")
    character_entity = relationship("Entity", foreign_keys=[character_entity_id], back_populates="knowledge_states")
    source_scene = relationship("Scene", foreign_keys=[source_scene_id], back_populates="knowledge_states")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    issue_type = Column(String(100), nullable=False)  # FACT_CONFLICT | LOCATION_CONFLICT | OBJECT_OWNERSHIP_CONFLICT | KNOWLEDGE_CONFLICT | etc.
    severity = Column(String(20), default="WARNING", nullable=False)  # INFO | WARNING | ERROR
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    status = Column(String(20), default="OPEN", nullable=False)  # OPEN | ACCEPTED | IGNORED | RESOLVED
    evidence_json = Column(JSON, default=list, nullable=False)
    
    # Day 4 Human-in-the-Loop Review Fields
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String(50), default="writer", nullable=True)
    resolution_type = Column(String(50), nullable=True)  # INTENTIONAL | FIXED | FALSE_POSITIVE | ACCEPTED_AS_IS | NEEDS_REVIEW
    resolution_note = Column(Text, nullable=True)
    issue_fingerprint = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="issues")
    scene = relationship("Scene", back_populates="issues")
    reviews = relationship("IssueReview", back_populates="issue", cascade="all, delete-orphan", order_by="IssueReview.created_at.desc()")


class IssueReview(Base):
    __tablename__ = "issue_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)  # ACCEPT | IGNORE | RESOLVE | REOPEN
    note = Column(Text, nullable=True)
    previous_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    issue = relationship("Issue", back_populates="reviews")
    project = relationship("Project", back_populates="issue_reviews")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(50), default="REAL_WORLD_CLAIM", nullable=False)  # REAL_WORLD_CLAIM | FICTIONAL_WORLD_RULE | STORY_FACT | UNVERIFIED_CLAIM
    subject = Column(String(255), nullable=True)
    predicate = Column(String(100), nullable=True)
    object = Column(String(255), nullable=True)
    temporal_context = Column(String(100), nullable=True)
    location_context = Column(String(100), nullable=True)
    requires_research = Column(Boolean, default=False, nullable=False)
    research_priority = Column(String(20), default="MEDIUM", nullable=False)  # HIGH | MEDIUM | LOW
    status = Column(String(30), default="UNVERIFIED", nullable=False)  # UNVERIFIED | RESEARCH_REQUESTED | VERIFIED | CONTRADICTED | INCONCLUSIVE | DISMISSED
    claim_fingerprint = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="claims")
    scene = relationship("Scene", back_populates="claims")
    research_tasks = relationship("ResearchTask", back_populates="claim", cascade="all, delete-orphan")


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    objective = Column(Text, nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING | RUNNING | COMPLETED | FAILED | CANCELLED
    provider = Column(String(50), default="parallel", nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="research_tasks")
    scene = relationship("Scene", back_populates="research_tasks")
    claim = relationship("Claim", back_populates="research_tasks")
    results = relationship("ResearchResult", back_populates="research_task", cascade="all, delete-orphan")
    evaluations = relationship("ResearchEvaluation", back_populates="research_task", cascade="all, delete-orphan")


class ResearchResult(Base):
    __tablename__ = "research_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_task_id = Column(String(36), ForeignKey("research_tasks.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False)
    excerpt = Column(Text, nullable=False)
    relevance_score = Column(Float, default=1.0, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    raw_metadata_json = Column(JSON, default=dict, nullable=False)

    # Relationships
    research_task = relationship("ResearchTask", back_populates="results")


class ResearchEvaluation(Base):
    __tablename__ = "research_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_task_id = Column(String(36), ForeignKey("research_tasks.id", ondelete="CASCADE"), nullable=False)
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    verdict = Column(String(50), nullable=False)  # VERIFIED | LIKELY_TRUE | CONTRADICTED | INCONCLUSIVE | INSUFFICIENT_EVIDENCE
    confidence = Column(Float, default=0.90, nullable=False)
    summary = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    supporting_source_ids_json = Column(JSON, default=list, nullable=False)
    contradicting_source_ids_json = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    research_task = relationship("ResearchTask", back_populates="evaluations")


class SceneAnalysisRun(Base):
    __tablename__ = "scene_analysis_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="COMPLETED", nullable=False)  # IDLE | ANALYZING | COMPLETED | PARTIAL | FAILED
    entities_count = Column(Integer, default=0, nullable=False)
    facts_count = Column(Integer, default=0, nullable=False)
    events_count = Column(Integer, default=0, nullable=False)
    issues_count = Column(Integer, default=0, nullable=False)
    claims_count = Column(Integer, default=0, nullable=False)
    research_reused_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    project = relationship("Project")
    scene = relationship("Scene")


class PlotEvent(Base):
    __tablename__ = "plot_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=True)
    event_id = Column(String(100), nullable=False)  # e.g. "scene_1_event_1"
    scene_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    track_type = Column(String(50), nullable=False)  # MAIN_PLOT | SUBPLOT
    track_name = Column(String(100), nullable=False)  # e.g. "Core Mystery"
    importance_score = Column(String(50), nullable=False)  # CRITICAL | HIGH | MEDIUM
    excerpt = Column(Text, nullable=False)
    connected_to_event = Column(String(100), nullable=True)
    connection_type = Column(String(50), nullable=True)  # TRIGGERS | CONVERGES_WITH | REVEALS | CONTRADICTS
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="plot_events")
    scene = relationship("Scene")


class ProjectSettings(Base):
    __tablename__ = "project_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    reality_level = Column(Integer, default=5, nullable=False)
    continuity_strictness = Column(Integer, default=5, nullable=False)
    auto_background_analysis_enabled = Column(Boolean, default=True, nullable=False)
    settings_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("reality_level >= 0 AND reality_level <= 10", name="chk_reality_level_bounds"),
        CheckConstraint("continuity_strictness >= 0 AND continuity_strictness <= 10", name="chk_continuity_strictness_bounds"),
    )

    # Relationships
    project = relationship("Project", back_populates="settings")


class StoryWorldRule(Base):
    __tablename__ = "story_world_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    rule_text = Column(Text, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="world_rules")


