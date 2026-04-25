"""Sources service for Sprint 2 CRUD."""

from typing import List

from app.core.seed_sources import get_seed_catalog_summary
from app.modules.sources.models import Source
from app.modules.sources.repository import SourceRepository
from app.modules.sources.schemas import SourceCreate, SourceUpdate


class SourceService:
	def __init__(self, repository: SourceRepository) -> None:
		self.repository = repository

	def list_sources(self) -> List[Source]:
		return self.repository.list_all()

	def list_active_sources(self) -> List[Source]:
		return self.repository.list_active()

	def get_default_catalog_summary(self) -> dict[str, int | bool]:
		return get_seed_catalog_summary()

	def create_source(self, source_data: SourceCreate) -> Source:
		existing_source = self.repository.get_by_url(str(source_data.url))
		if existing_source:
			raise ValueError("A source with this URL already exists.")

		return self.repository.create(source_data)

	def get_source(self, source_id: int) -> Source:
		source = self.repository.get_by_id(source_id)
		if not source:
			raise ValueError("Source not found.")
		return source

	def update_source(self, source_id: int, source_data: SourceUpdate) -> Source:
		source = self.get_source(source_id)

		if source_data.url is not None:
			existing_source = self.repository.get_by_url(str(source_data.url))
			if existing_source and existing_source.id != source.id:
				raise ValueError("A source with this URL already exists.")

		return self.repository.update(source, source_data)

	def delete_source(self, source_id: int) -> None:
		source = self.get_source(source_id)
		self.repository.delete(source)

	def activate_source(self, source_id: int) -> Source:
		source = self.get_source(source_id)
		source.is_active = True
		return self.repository.update(source, SourceUpdate(is_active=True))

	def deactivate_source(self, source_id: int) -> Source:
		source = self.get_source(source_id)
		source.is_active = False
		return self.repository.update(source, SourceUpdate(is_active=False))
