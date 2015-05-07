import sys
sys.path.append('..')

import json
from tagger import tag
import readers


def excel_test():
    fname = sys.argv[1] if len(sys.argv) > 1 else '../data/sample.xlsx'
    class_hint, properties, entities = readers.xls(fname)
    results = tag(
        class_hint=class_hint,
        entities=entities,
        properties=properties)
    print json.dumps(results, indent=2)


if __name__ == '__main__':
    excel_test()
