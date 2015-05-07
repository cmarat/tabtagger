import gzip
import itertools
import json
import os
import sys
import time
import pymongo

sys.path.append('..')
from tagger import tag


string_ok = lambda s: len([l for l in s if l.isalpha()]) > 0
sequence_ok = lambda l: len([1 for s in l if string_ok(s)]) > len(l) / 2 + 1


def find_header(relation):
    for col in relation[:3]:
        if sequence_ok(col):
            return list(col)
    return []


def candidates(fname):
    if os.path.splitext(fname)[1] == '.gz':
        lines = gzip.open(fname)
    else:
        lines = open(fname)

    for i, line in enumerate(lines):
        data = json.loads(line)
        if data['tableType'] == 'RELATION':
            hleft = find_header(data['relation'])
            htop = find_header(zip(*data['relation']))
            if len(hleft) > 2:
                yield {
                    'source': '{}:{}'.format(fname, i),
                    'data': data,
                    'hleft': hleft,
                    'htop': htop,
                }


def tag_candidate(table_data, max_entities=None):
    t0 = time.time()
    hint = table_data['hleft'][0]
    result = tag(
        class_hint=hint,
        entities=table_data['hleft'][:max_entities],
        properties=table_data['htop'][:max_entities])
    if (result['tags'] and result['total_labels'] > 4
            and result['matched_labels'] > 3):
        table_data['tagged'] = True
        result['timestamp'] = time.time()
        result['runtime'] = time.time() - t0
        table_data['results'] = result
    else:
        table_data['tagged'] = False
    return table_data


def load(fname):
    dwtc = pymongo.MongoClient().dwtc.test
    tagged = (tag_candidate(c, max_entities=100) for c in candidates(fname))
    tagged_ok = (d for d in tagged if d['tagged'])
    sample = itertools.islice(tagged_ok, 0, 10)
    for s in sample:
        dwtc.insert(s)

    # for d in itertools.islice(tagged, 1, 100):
    #     if d['tagged']:
    #         print json.dumps(d['results'], indent=2)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        load(sys.argv[1])
    else:
        load('../data/dwtc-000-sample1.json')
