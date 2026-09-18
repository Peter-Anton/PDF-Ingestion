from .VectorDBEnum import VectorDBEnum
from .providers import QuadrantDB
from controllers.BaseController import BaseController
class VectorDBProviderFactory:
    def __init__(self, config:dict):
        self.config=config
        self.base_controller = BaseController()
    def create(self,provider:str):
       pass