from abc import ABC, abstractmethod

class EmbeddingInterface(ABC):
    @abstractmethod
    def set_embedding_model(self,model_id:str, embed_size:int):
        pass
    @abstractmethod
    def process_text(self,text:str):
        pass
    @abstractmethod
    def get_embedding_size(self) -> int:
        pass
    @abstractmethod
    def embed_text(self,text:str,document_type:str):
        pass


