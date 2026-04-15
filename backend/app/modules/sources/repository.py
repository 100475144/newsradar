"""Sources repository for Sprint 2 CRUD."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.sources.models import Source
from app.modules.sources.schemas import SourceCreate, SourceUpdate


class SourceRepository:
	def __init__(self, db: Session) -> None:
		self.db = db

	def get_by_id_and_owner(self, source_id: int, owner_id: int) -> Optional[Source]:
		return (
			self.db.query(Source)
			.filter(Source.id == source_id, Source.created_by == owner_id)
			.first()
		)

	def get_by_url_and_owner(self, url: str, owner_id: int) -> Optional[Source]:
		normalized_url = str(url).strip()
		return (
			self.db.query(Source)
			.filter(Source.url == normalized_url, Source.created_by == owner_id)
			.first()
		)

	def list_by_owner(self, owner_id: int) -> List[Source]:
		return (
			self.db.query(Source)
			.filter(Source.created_by == owner_id)
			.order_by(Source.created_at.desc())
			.all()
		)

	def create(self, source_data: SourceCreate, owner_id: int) -> Source:
		source = Source(
			name=source_data.name.strip(),
			url=str(source_data.url),
			category=source_data.category,
			created_by=owner_id,
		)
		self.db.add(source)
		self.db.commit()
		self.db.refresh(source)
		return source

	def update(self, source: Source, source_data: SourceUpdate) -> Source:
		updates = source_data.model_dump(exclude_unset=True)
		for field, value in updates.items():
			if field == "name" and isinstance(value, str):
				value = value.strip()
			elif field == "url" and value is not None:
				value = str(value)
			setattr(source, field, value)

		self.db.add(source)
		self.db.commit()
		self.db.refresh(source)
		return source

	def delete(self, source: Source) -> None:
		self.db.delete(source)
		self.db.commit()
