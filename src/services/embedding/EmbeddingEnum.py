from enum import Enum
class EmbeddingEnum(Enum):
    """
    Enum class for Embedding providers.
    """
    LOCAL="LOCAL"

class LocalEnum(Enum):
    DOCUMENT="search_document"
    QUERY="search_query"

class documentTypeEnum(Enum):
    """
    Enum class for document types.
    """
    DOCUMENT="document"
    QUERY="query"    