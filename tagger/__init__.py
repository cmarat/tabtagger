import rank
import lookup


def tag(entities=[], properties=[], class_hint='', extended_info=True):
    hint = dict.fromkeys(lookup.class_match(class_hint), 1)
    classes = lookup.classes_match(entities)
    classes_rank = rank.superclass_rank(classes)
    domains = lookup.domains(properties)
    domain_ranks = rank.domain_rank(domains)
    combined_rank = rank.combined_rank(classes_rank, domain_ranks, hint)
    if extended_info:
        return {
            "tags": combined_rank,
            "total_labels": len(entities),
            "matched_labels": len(classes)
        }
    else:
        return {
            "tags": combined_rank
        }
