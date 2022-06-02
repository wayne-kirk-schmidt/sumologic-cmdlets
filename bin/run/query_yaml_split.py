#!/usr/bin/env python3
"""
Sample YAML extractor of query strings into .sqy
"""
import os
import re
import sys
from benedict import benedict

yaml_file = sys.argv[1]
yaml_dir = os.path.dirname(os.path.abspath(yaml_file))
yaml_dict = benedict.from_yaml(yaml_file)

for keypath in benedict.keypaths(yaml_dict):
    if re.match(r".*?\.query$", keypath):
        query_file = os.path.join(yaml_dir, keypath + '.sqy')
        print(query_file)
        with open(query_file, 'w', encoding='utf8') as file_object:
            file_object.write(yaml_dict[keypath])
