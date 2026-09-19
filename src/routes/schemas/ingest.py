from pydantic import BaseModel
class IngestResponse(BaseModel):
    message: str
    files: list[str]
