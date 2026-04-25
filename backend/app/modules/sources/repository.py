"""Sources repository for the global source catalog."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.sources.models import Source
from app.modules.sources.schemas import SourceCreate, SourceUpdate


class SourceRepository:
	def __init__(self, db: Session) -> None:
		self.db = db

	def get_by_id(self, source_id: int) -> Optional[Source]:
		return self.db.query(Source).filter(Source.id == source_id).first()


	def get_by_url(self, url: str) -> Optional[Source]:
		normalized_url = str(url).strip()
		return self.db.query(Source).filter(Source.url == normalized_url).first()

	def list_all(self) -> List[Source]:
		return (
            self.db.query(Source)
            .order_by(Source.medium_name.asc(), Source.name.asc(), Source.created_at.desc())
            .all()
        )

	def list_active(self) -> List[Source]:
		return (
            self.db.query(Source)
            .filter(Source.is_active == True)  # noqa: E712
            .order_by(Source.medium_name.asc(), Source.name.asc(), Source.created_at.desc())
            .all()
        )

	def create(self, source_data: SourceCreate) -> Source:
		source = Source(
            medium_name=source_data.medium_name.strip(),
            name=source_data.name.strip(),
            url=str(source_data.url),
            category=source_data.category,
        )
		self.db.add(source)
		self.db.commit()
		self.db.refresh(source)
		return source

	def update(self, source: Source, source_data: SourceUpdate) -> Source:
		updates = source_data.model_dump(exclude_unset=True)
		for field, value in updates.items():
			if field in {"medium_name", "name"} and isinstance(value, str):
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
