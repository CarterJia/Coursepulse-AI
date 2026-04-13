from pydantic import BaseModel


class GlossaryEntryResponse(BaseModel):
    id: str
    term: str
    definition: str
    analogy: str | None = None
