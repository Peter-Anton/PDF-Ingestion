
import logging
import ollama
from services.embedding.EmbeddingEnum import LocalEnum, documentTypeEnum
from services.embedding.EmbeddingInterface import EmbeddingInterface

logger = logging.getLogger(__name__)


class LocalProvider(EmbeddingInterface):
    """Local embedding provider using sentence-transformers."""
    def __init__(self,
                 default_input_max_characters: int=1000,
                 default_output_max_characters: int=1000,
                 temperature: float=0.1,
                 model_name: str="nomic-embed-text"
                 ):
            self.default_input_max_characters = default_input_max_characters
            self.default_output_max_characters = default_output_max_characters
            self.temperature = temperature
            self.embedding_model_id = None
            self.embed_size=None
            self.model_name = model_name
            self.client = ollama
            self.logger = logging.getLogger(__name__)
    def set_embedding_model(self, model_id: str, embed_size: int):
        self.embedding_model_id = model_id
        self.embed_size = embed_size
    def get_embedding_size(self) -> int:
         return self.embed_size
    
    def process_text(self,text:str):
            return text[:self.default_input_max_characters].strip()
    
    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("Ollama client was not set")
            return None

        model_name = self.embedding_model_id or self.model_name
        try:
            response = self.client.embed(
                model=model_name,
                input=self.process_text(text),
            )
            embeddings = response["embeddings"] if isinstance(response, dict) else response.embeddings
            embedding = embeddings[0] if embeddings and isinstance(embeddings[0], (list, tuple)) else embeddings
        except Exception:
            self.logger.exception("Error while embedding text with Ollama model %s", model_name)
            return None

        if not embedding:
            self.logger.error("Ollama returned an empty embedding")
            return None

        return embedding