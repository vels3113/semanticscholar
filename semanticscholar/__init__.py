import json
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

with open('swagger.json') as swagger:
    API_info = json.load(swagger)

API_definitions = API_info['definitions']
paper_fields = API_definitions['FullPaper']['properties']
author_fields = API_definitions['Author']['properties']
API_errors = {key[6:] : API_definitions[key] for key in API_definitions.keys() if key[:5] == "Error"}

from .restful import paper, author
from .SemanticScholar import SemanticScholar