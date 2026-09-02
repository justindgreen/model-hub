from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class ModelTagLink(SQLModel, table=True):
    model_id: Optional[int] = Field(default=None, foreign_key="model3d.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class ModelCollectionLink(SQLModel, table=True):
    model_id: Optional[int] = Field(default=None, foreign_key="model3d.id", primary_key=True)
    collection_id: Optional[int] = Field(default=None, foreign_key="collection.id", primary_key=True)


class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    ai_generated: bool = False
    models: List["Model3D"] = Relationship(back_populates="tags", link_model=ModelTagLink)


class Collection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="collection.id")
    models: List["Model3D"] = Relationship(back_populates="collections", link_model=ModelCollectionLink)


class SmartCollection(SQLModel, table=True):
    """Rule-based auto-filing collection. rule_json example:
    {"match": "all", "conditions": [{"field": "tag", "op": "contains", "value": "vase"}]}
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    rule_json: str


class Model3D(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    path: str = Field(index=True, unique=True)
    extension: str
    size_bytes: int
    content_hash: str = Field(index=True)
    geometry_hash: Optional[str] = Field(default=None, index=True)
    thumbnail_path: Optional[str] = None
    vertex_count: Optional[int] = None
    face_count: Optional[int] = None
    bbox_x: Optional[float] = None
    bbox_y: Optional[float] = None
    bbox_z: Optional[float] = None
    volume_mm3: Optional[float] = None
    is_watertight: Optional[bool] = None

    # roadmap: metadata / provenance tracking
    source_url: Optional[str] = None
    designer: Optional[str] = None
    license: Optional[str] = None

    is_duplicate_of: Optional[int] = Field(default=None, foreign_key="model3d.id")

    ai_tagged: bool = False
    ai_description: Optional[str] = None
    embedding: Optional[bytes] = None  # float32 vector, packed

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_scanned_at: datetime = Field(default_factory=datetime.utcnow)

    tags: List[Tag] = Relationship(back_populates="models", link_model=ModelTagLink)
    collections: List[Collection] = Relationship(back_populates="models", link_model=ModelCollectionLink)


class Filament(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    material: str  # PLA, PETG, ABS, ...
    brand: Optional[str] = None
    color: Optional[str] = None
    color_hex: Optional[str] = None
    spool_weight_g: float = 1000
    remaining_g: float = 1000
    purchase_url: Optional[str] = None
    notes: Optional[str] = None


class QueueItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: int = Field(foreign_key="model3d.id")
    position: int = 0
    status: str = "queued"  # queued, printing, done, failed
    filament_id: Optional[int] = Field(default=None, foreign_key="filament.id")
    notes: Optional[str] = None
    estimated_grams: Optional[float] = None
    estimated_minutes: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AppSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
