from enum import Enum

class VectorDBEnum(Enum):
    QDRANT = "Qdrant"
class DistanceMethodeEnum(Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"    