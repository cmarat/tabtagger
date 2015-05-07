import json
import os
import rdflib
from collections import defaultdict

RDFS = rdflib.namespace.RDFS
DBPEDIA_JSON = os.path.join(os.path.dirname(__file__), 'dbpedia_2014.json')


class Ontology(object):
    def __init__(self, filename=''):
        if not filename:
            return
        _, ext = os.path.splitext(filename)
        if ext == '.json' or ext == '.js':
            self.from_json(filename)
        else:
            self.from_rdf(filename)

    def from_rdf(self, filename):
        g = rdflib.Graph()
        g.parse(filename)
        self.pred = defaultdict(set)
        self.succ = defaultdict(set)
        classes = g.subject_objects(predicate=RDFS['subClassOf'])
        for subclass, superclass in classes:
                self.pred[str(subclass)].add(str(superclass))
                self.succ[str(superclass)].add(str(subclass))
        self.domain = {str(prop): str(domain)
                       for prop, domain
                       in g.subject_objects(predicate=RDFS['domain'])}

    def from_json(self, filename):
        stored = json.load(open(filename))
        self.pred = defaultdict(set)
        self.succ = defaultdict(set)
        self.pred.update(((k, set(v)) for k, v in stored['pred'].iteritems()))
        self.succ.update(((k, set(v)) for k, v in stored['succ'].iteritems()))
        self.domain = stored['domain']

    def superclasses(self, klass, include_distance=False):
        return _traverse_dict(
            self.pred, klass, include_distance)

    def subclasses(self, klass, include_distance=False):
        return _traverse_dict(
            self.succ, klass, include_distance)

    def specific(self, classes):
        _classes = set(classes)
        superclasses = set()
        for c in _classes:
            sc = set(self.superclasses(c))
            sc.remove(c)
            superclasses |= sc
        return _classes - superclasses


def _traverse_dict(d, start, include_distance=False):
    level = 0
    result = []
    nextlevel = [start]
    while nextlevel:
        thislevel = nextlevel
        if include_distance:
            result.extend([(n, level) for n in thislevel])
        else:
            result.extend(thislevel)
        nextlevel = []
        for node in thislevel:
            nextlevel.extend(d[node])
        level += 1
    return result


def default_ontology():
    return Ontology(DBPEDIA_JSON)


def convert_ontology(fname):
    dbo = Ontology(fname)
    json.dump(
        {
            'pred': {k: list(v) for k, v in dbo.pred.iteritems()},
            'succ': {k: list(v) for k, v in dbo.succ.iteritems()},
            'domain': dbo.domain
        },
        open(DBPEDIA_JSON, 'w'))


def main():
    import sys
    print "Converting RDF ontology to JSON"
    if len(sys.argv) > 1:
        convert_ontology(sys.argv[1])
        print "Done"
    else:
        print "ERROR: Expecting RDF ontology as command line parameter"


if __name__ == '__main__':
    main()
