from stores.llm.LLMEnum import LLMEnum
from .providers import openAIProvider
from .providers import CohereProvider
class LLMProviderFactory:
    def __init__(self, config):
        self.config=config
    def create(self,provider:str):
        if provider == LLMEnum.OPENAI.value:
            return openAIProvider.OpenAIProvider(
                api_key=self.config.OPENAI_API_KEY,
                default_input_max_characters=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_output_max_characters=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                temperature=self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        return None