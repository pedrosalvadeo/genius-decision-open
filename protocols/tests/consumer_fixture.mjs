// Independent finite H=0 fixture authored for the external Node consumer.
// Equal lexical IDs deliberately inhabit distinct nominal namespaces.
export const LARGE_Q = '9007199254740993/9007199254740992';
export const NEGATIVE_Q = '-9007199254740993/9007199254740992';
export function makeFixture() {
  const basis = ['Premise'];
  const queries = ['PZ', 'PA'].map(policy => ({ policy, path: [] }));
  return {
    format: 'genius-fp1/1.0',
    meta: { id: 'ConsumerFixture', framework: 'Framework', model: 'Model', context: 'Context', condition: 'Condition', horizon: '0', specification: 'GENIUS-SPEC-1.0.0', theory_snapshot: 'GENIUS-THEORY-2026-09-23-S2', profile: 'FP1_FINITE_EXACT', claim_scope: 'FORMAL_INSTANCE_ONLY' },
    assumptions: [{ id: 'Premise', kind: 'SYNTHETIC', statement: 'Supuesto: agua, 水, 🧪; é / e\u0301; línea\nsegunda.', provenance: 'Consumer fixture; no empirical claim.' }],
    initialization: { history: 'History', condition: 'Condition', x0: 'Shared', i0: 'Shared', basis },
    model: { states: ['Shared'], information: ['Shared'], actions: [], observations: [], exogenous: [], basis, information_basis: basis, executable: [], admissible: [], transitions: [], updates: [] },
    policies: queries.map(q => ({ id: q.policy, decisions: [] })),
    scenarios: [{ id: 'Scenario', inputs: [] }],
    functional: { indices: [{ id: 'Index', calibration: [{ raw: LARGE_Q, value: LARGE_Q }], basis }], measurements: [{ t: '0', x: 'Shared', index: 'Index', raw: LARGE_Q }], reduction: { ids: ['Reduced'], rows: [{ t: '0', x: 'Shared', reduced: 'Reduced' }] } },
    composition: { ports: [], rows: queries.map(query => ({ query, values: [] })), views: [{ id: 'View', columns: ['query'] }], basis },
    resources: { kinds: [{ id: 'Shared', unit: 'Unit' }], demands: [{ id: 'Demand', resource: 'Shared', unit: 'Unit', basis }], values: queries.map(query => ({ query, demand: 'Demand', value: LARGE_Q })), basis },
    generative: { native_ids: ['Shared'], common_ids: ['Shared'], meaning_atoms: ['Atom'], native_meaning: [{ identity: 'Shared', atoms: ['Atom'] }], common_meaning: [{ identity: 'Shared', atoms: ['Atom'] }], native_order: [['Shared', 'Shared']], common_order: [['Shared', 'Shared']], identity: [{ t: '0', x: 'Shared', native: 'Shared' }], translation: [{ native: 'Shared', common: 'Shared' }], recipe: { kind: 'att' }, mode: 'robust', basis },
    welfare: { carriers: ['Shared'], dimensions: [{ id: 'Dimension', basis }], existence: [{ t: '0', carrier: 'Shared' }], applicability: [{ t: '0', carrier: 'Shared', dimension: 'Dimension' }], values: queries.map(query => ({ query, carrier: 'Shared', dimension: 'Dimension', value: NEGATIVE_Q })), basis },
    semantics: { states: ['Good'], references: queries.map(leaf => ({ leaf, states: ['Good'] })), task: [{ state: 'Good', value: '1' }], protocol: 'FP1_EXACT_ENUM_V1', basis },
    law: { rows: [], basis },
    constraints: [{ id: 'Budget', kind: 'resource_budget', resource: 'Shared', bound: LARGE_Q, basis }],
    selection: { mode: 'unique' },
  };
}
