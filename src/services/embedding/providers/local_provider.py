
import logging
import os

from fastembed import TextEmbedding
from services.embedding.EmbeddingInterface import EmbeddingInterface

logger = logging.getLogger(__name__)


class LocalProvider(EmbeddingInterface):
    """Local embedding provider using FastEmbed and an ONNX model."""
    def __init__(self,
                 default_input_max_characters: int=1000,
                 model_name: str="BAAI/bge-small-en-v1.5"
                 ):
            self.default_input_max_characters = default_input_max_characters
            self.embedding_model_id = None
            self.embed_size=None
            self.model_name = model_name
            self.client = None
            self.logger = logging.getLogger(__name__)
    def set_embedding_model(self, model_id: str, embed_size: int):
        self.embedding_model_id = model_id
        self.embed_size = embed_size
        self.client = TextEmbedding(
            model_name=model_id or self.model_name,
            cache_dir=os.getenv("FASTEMBED_CACHE_PATH", "/models"),
        )
    def get_embedding_size(self) -> int:
         return self.embed_size
    
    def process_text(self,text:str):
            return text[:self.default_input_max_characters].strip()
    
    def embed_text(self, text: str, document_type: str = None):
        return self.embed_texts([text], document_type)[0]

    def embed_texts(self, texts: list[str], document_type: str = None):
        if not self.client:
            raise RuntimeError("Embedding model has not been initialized")

        try:
            embeddings = list(
                self.client.embed([self.process_text(text) for text in texts])
            )
        except Exception:
            self.logger.exception("Error while embedding text with model %s", self.embedding_model_id)
            raise

        if len(embeddings) != len(texts):
            raise RuntimeError(f"Embedding model returned {len(embeddings)} vectors; expected {len(texts)}")

        vectors = []
        for embedding in embeddings:
            if embedding is None or len(embedding) != self.embed_size:
                raise RuntimeError(
                    f"Embedding model returned {len(embedding)} values; expected {self.embed_size}"
                )
            vectors.append(embedding.tolist())
        return vectors