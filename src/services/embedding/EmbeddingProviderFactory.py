from embedding.EmbeddingEnum import EmbeddingEnum
from .providers.local_provider import LocalProvider

class EmbeddingProviderFactory:
    def __init__(self, config):
        self.config=config
    def create(self,provider:str):
        if provider == EmbeddingEnum.LOCAL.value:
            return LocalProvider(
                api_key=self.config.OPENAI_API_KEY,
                default_input_max_characters=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_output_max_characters=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                temperature=self.config.GENERATION_DEFAULT_TEMPERATURE,
                model_name=self.config.EMBEDDING_MODEL_ID
            )
        return None