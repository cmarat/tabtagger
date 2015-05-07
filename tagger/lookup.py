from collections import defaultdict
from SPARQLWrapper import SPARQLWrapper, JSON

# sparql = SPARQLWrapper("http://dbpedia.org/sparql")
sparql = SPARQLWrapper("http://localhost:8890/sparql")
sparql.method = 'POST'
sparql.setReturnFormat(JSON)


def sanitized(literal):
    unsafe = ['\\', '"', "'", '\n', '\r']
    return ''.join([
        ('\u00{}'.format(hex(ord(c))[2:]) if c in unsafe else c)
        for c in literal
    ])


def lookup(label_list, constraint=''):
    labels = ', '.join([u'"{}"@en'.format(sanitized(l)) for l in label_list])
    query = ur"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX dbpedia: <http://dbpedia.org/resource/>
        PREFIX dbp: <http://dbpedia.org/property/>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT distinct * WHERE {{
          ?uri rdfs:label ?label .
          filter(?label in ({labels})) .
          {constraint}
        }}
        """.format(labels=labels, constraint=constraint)
    sparql.setQuery(query)
    try:
        result = sparql.query()
    except Exception as e:
        print "ERROR while executing SPARQL query:\n{}".format(e)
        return {}
    return LookupResults(result)


def classes_match(label_list):
    result = lookup(
        label_list,
        constraint=ur"""
            FILTER (strstarts(str(?uri), "http://dbpedia.org/")) .
            OPTIONAL {
                ?uri a ?class .
                # trick for filtering out non-dbpedia classes:
                ?class rdfs:label [] .
            }
            # possibly virtuoso bug: the query returns empty result
            # when dbo:wikiPageRedirects are not loaded
            # MINUS {
            #    ?uri (dbo:wikiPageRedirects | dbo:wikiPageDisambiguates) []
            # } .
            """)
    class_info = []
    for v in result.values():
        c = v.get('class', [])
        class_info.append(c)
    return class_info


def domains(label_list):
    if not label_list:
        return []
    result = lookup(
        label_list,
        constraint=ur"""
            ?uri a rdf:Property
            #    ;rdfs:isDefinedBy <http://dbpedia.org/ontology/> .
            OPTIONAL {?uri rdfs:domain ?domain}""")
    domains = [v['domain'][0] for v in result.values() if 'domain' in v]
    return domains


def class_match(label):
    if not label:
        return {}
    _label = u'"{}"@en'.format(sanitized(label))
    query = ur"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT distinct ?class WHERE {{
          ?class a owl:Class
            # ; rdfs:isDefinedBy <http://dbpedia.org/ontology/>
            ; rdfs:label {label} .
        }}
        """.format(label=_label)
    sparql.setQuery(query)
    bindings = sparql.queryAndConvert()["results"]["bindings"]
    return [b['class']['value'] for b in bindings]


class LookupResults(dict):
    """docstring for LookupResults"""
    def __init__(self, query_result):
        super(LookupResults, self).__init__()
        self.update(normalize_bindings(
            query_result.convert()["results"]["bindings"]))


def normalize_bindings(bindings):
    aggr = defaultdict(lambda: defaultdict(set))
    for binding in bindings:
        label = binding.pop('label')['value']
        for p, v in binding.items():
            aggr[label][p].add(v['value'])
    return {
        k: {p: list(o) for p, o in v.iteritems()}
        for k, v in aggr.iteritems()}
