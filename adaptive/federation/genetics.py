"""Data-only, bounded hereditary traits. Neither code nor authority is a gene."""
from copy import deepcopy

from .core import canonical, digest, fields, identifier, integer

CONSTITUTION = {
    'format': 'genius-constitution/1',
    'purpose': 'Improve understanding and conditions for wellbeing and sustained life',
    'invariants': ['representation_is_not_reality', 'evidence_is_not_inference',
                   'unknown_probability_stays_unknown', 'scope_includes_declared_affected_systems',
                   'evaluate_trajectories_not_only_endpoints', 'operational_error_is_not_wellbeing'],
    'selection': 'lower_posterior_error_with_no_worse_maximum_error_then_prospective_confirmation',
    'authority': 'host_permissions_and_budgets_are_external_to_genes',
    'executable_mutation': False,
}
CONSTITUTION_HASH = digest(CONSTITUTION)
ALLELES = {'estimator': ('lower_median', 'mean_floor', 'last_value'), 'window': (3, 5, 9)}
DEFAULT = {'estimator': 'lower_median', 'window': 5}
MAX_GENERATION = 32


def validate(genome):
    fields(genome, 'format constitution_sha256 genes generation parents origin event')
    if genome['format'] != 'genius-genome/1' or genome['constitution_sha256'] != CONSTITUTION_HASH:
        raise ValueError('CONSTITUTION_MISMATCH')
    fields(genome['genes'], 'estimator window')
    if (type(genome['genes']['window']) is not int or
        any(genome['genes'][name] not in values for name, values in ALLELES.items())):
        raise ValueError('UNSUPPORTED_ALLELE')
    integer(genome['generation'], MAX_GENERATION); identifier(genome['event'])
    parents = genome['parents']
    if type(parents) is not list or len(parents) > 2 or any(not isinstance(p,str) for p in parents) or len(set(parents)) != len(parents):
        raise ValueError('INVALID_PARENTS')
    for parent in parents:
        if not isinstance(parent, str) or len(parent) != 64 or any(c not in '0123456789abcdef' for c in parent):
            raise ValueError('INVALID_PARENT_HASH')
    counts = {'FOUNDER': 0, 'INHERITANCE': 1, 'MUTATION': 1, 'RECOMBINATION': 2}
    if not isinstance(genome['origin'],str) or genome['origin'] not in counts or len(parents) != counts[genome['origin']]:
        raise ValueError('INVALID_ORIGIN')
    if (genome['generation'] == 0) != (genome['origin'] == 'FOUNDER'):
        raise ValueError('INVALID_GENERATION')
    return genome


def make(genes, parents, origin, event):
    for parent in parents: validate(parent)
    result = dict(format='genius-genome/1', constitution_sha256=CONSTITUTION_HASH,
                  genes=deepcopy(genes), generation=1+max((p['generation'] for p in parents), default=-1),
                  parents=[digest(p) for p in parents], origin=origin, event=event)
    return validate(result)


def founder(event):
    return make(DEFAULT, [], 'FOUNDER', event)


def inherit(parent, event):
    return make(parent['genes'], [parent], 'INHERITANCE', event)


def mutate(parent, locus, allele, event):
    validate(parent)
    if locus not in ALLELES or allele == parent['genes'][locus]:
        raise ValueError('SINGLE_CHANGED_LOCUS_REQUIRED')
    genes = deepcopy(parent['genes']); genes[locus] = allele
    return make(genes, [parent], 'MUTATION', event)


def variants(parent, event):
    validate(parent)
    if parent['generation'] >= MAX_GENERATION: return []
    return [mutate(parent, name, value, digest([event, name, value]))
            for name, values in ALLELES.items() for value in values if value != parent['genes'][name]]


def recombine(first, second, event):
    """Local data operation; the resulting candidate still requires evaluation."""
    validate(first); validate(second)
    return make(dict(estimator=first['genes']['estimator'], window=second['genes']['window']),
                [first, second], 'RECOMBINATION', event)


def express(genome, evidence):
    """Evidence must already pass context, conflict, validity and provenance checks."""
    validate(genome)
    if not evidence: raise ValueError('INSUFFICIENT_EVIDENCE')
    ordered = sorted(evidence, key=lambda row: (row['observed_at'], row['event'], row['hash']))
    # Keep simultaneous events together at the cutoff; all remain within Node's memory limit.
    cutoff = ordered[max(0,len(ordered)-genome['genes']['window'])]['observed_at']
    rows = [row for row in ordered if row['observed_at'] >= cutoff]
    values = [row['value'] for row in rows]
    for value in values: integer(value)
    method = genome['genes']['estimator']
    if method == 'last_value':
        # An arbitrary event hash must not decide between simultaneous measurements.
        latest = [r['value'] for r in rows if r['observed_at'] == rows[-1]['observed_at']]
        value = sorted(latest)[(len(latest)-1)//2]
    elif method == 'mean_floor': value = sum(values)//len(values)
    else: value = sorted(values)[(len(values)-1)//2]
    return dict(estimate=value, genome_sha256=digest(genome), genes=deepcopy(genome['genes']),
                evidence_sha256=digest(rows), evidence_count=len(rows), probability=None)
