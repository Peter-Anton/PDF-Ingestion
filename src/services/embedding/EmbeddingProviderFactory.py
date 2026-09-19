from .EmbeddingEnum import EmbeddingEnum
from .providers.local_provider import LocalProvider

class EmbeddingProviderFactory:
    @staticmethod
    def create(provider: str):
        if provider == EmbeddingEnum.LOCAL.value:
            return LocalProvider()
        return None