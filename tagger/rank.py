from __future__ import division
from collections import Counter
from ontology import default_ontology


ontology = default_ontology()


# def merge(dict1, dict2, extend=True):
#     shared_keys = [k for k in dict1 if k in dict2]
#     result = dict1.copy()
#     for k in shared_keys:
#         result[k] += dict2[k]
#     if extend:
#         for k in dict2:
#             if k not in dict1:
#                 result[k] = dict2[k]
#     return result


def merge(dict1, dict2, extend=True):
    dict1 = dict(dict1)
    dict2 = dict(dict2)
    shared_keys = [k for k in dict1 if k in dict2]
    result = dict1.copy()
    for k in shared_keys:
        result[k] += dict2[k]
    if extend:
        for k in dict2:
            if k not in dict1:
                result[k] = dict2[k]
    return result.items()


def normalized(func):
    def inner(*arg, **kwarg):
        result = func(*arg, **kwarg)
        if result:
            norm = 1. / max(zip(*result)[1] or [1])
            return [(k, v * norm) for k, v in result]
        return []
    return inner


def ordered(func):
    def inner(*arg, **kwarg):
        result = func(*arg, **kwarg)
        return sorted(
            result, key=lambda i: i[1], reverse=True)
    return inner


@ordered
@normalized
def superclass_rank(class_info):
    decay = 0.7
    # For each recognized entity assign scores to classes which are
    # specific for this entity.
    if not class_info:
        return {}
    specific_score = Counter()
    for entity_classes in class_info:
        specific_classes = ontology.specific(entity_classes)
        if not specific_classes:
            continue
        confidence = 1.0 / len(specific_classes)
        for c in specific_classes:
            specific_score[c] += confidence
    for c in specific_classes:
        specific_score[c] **= 0.3

    # Assign scores to parent classes, keep track of specific classes
    # contributing to the score.
    cumulative_score = {}
    for c in specific_score:
        for parent, distance in ontology.superclasses(c, include_distance=True):
            score = cumulative_score.setdefault(
                parent, {'sources': set(), 'score': 0})
            score['score'] += specific_score[c] * (decay ** distance)
            score['sources'].add(c)

    # Find the highest score for each set of contributing specific classes.
    scores_by_source = {}
    for c, v in cumulative_score.items():
        source = tuple(sorted(v['sources']))
        max_score = scores_by_source.get(
            source, {'class': None, 'score': 0})['score']
        if max_score < v['score']:
            scores_by_source[source] = {'class': c, 'score': v['score']}
    return [(v['class'], v['score']) for v in scores_by_source.values()]


@normalized
def domain_rank(domains):
    _domains = []
    for c in domains:
        _domains.extend(ontology.subclasses(c))
    return Counter(_domains).items()


@ordered
@normalized
def combined_rank(classes_rank=[], domains_rank=[], hint_rank=[]):
    return merge(
        merge(classes_rank, hint_rank, extend=True),
        domains_rank,
        extend=False)
