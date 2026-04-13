from app.models.document import Document
from app.models.job import Job
from app.models.knowledge_chunk import KnowledgeChunk


def test_core_models_expose_expected_tablenames():
    assert Document.__tablename__ == "documents"
    assert KnowledgeChunk.__tablename__ == "knowledge_chunks"
    assert Job.__tablename__ == "jobs"
