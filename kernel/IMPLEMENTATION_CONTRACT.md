# F2 code coordination contract

This is an implementation design, subordinate to the immutable F1 specification in ../baseline/GENIUS_PHASE_1_HANDOFF. Python >=3.11, standard library only, fractions.Fraction, no network. Package genius_kernel; commands via python -m genius_kernel. Specification remains GENIUS-SPEC-1.0.0 until an explicitly reviewed amendment is needed.

Root owns common.py, engine.py, decision.py, verifier.py, __main__.py, packaging/docs. Schema/causal author owns schema.py and causal.py. Structural author owns structural.py. Evidence author owns evidence.py. Test author owns tests/ and executed case fixtures. Never edit another author's files without coordination. Report a specification gap before choosing new semantics.

## Shared Python API (root implements common.py)

- `qkey(query)` -> `(policy,tuple(path))`; `query(policy,path)` -> wire Query; `point(t,x)` -> Point with str(t); `qstr(Fraction)` -> canonical n/d.
- `defined(cell)` is bool state==DEFINED; `value(cell,default=None)` extracts only if DEFINED.
- `Context(data,raw,limits)` has `.data`, `.raw`, `.digest`, `.H` int, `.checks` list, `.diagnostics` list, `.facts` dict for coordination, `.completed_policies` set, `.expanded_nodes` int.
- `ctx.check(rule,outcome,*,policy=None,queries=(),points=(),support=None,detail='')` -> unique Check ID. outcome PASS/FAIL/UNDETERMINED. Default support cites entire INPUT pointer ''. scope lists are copied.
- `ctx.diag(code,component,*,policy=None,queries=(),points=(),pointers=(),message='')` -> unique Diagnostic ID; pointers are INPUT JSON Pointer strings.
- `ctx.ok(value,rule,**check_kwargs)` -> DEFINED Cell with new PASS Check.
- `ctx.out(code,component,rule,**scope_kwargs)` -> OUTSIDE_DOMAIN with diagnostic and FAIL Check; `ctx.block(code,component,**scope_kwargs)` -> BLOCKED with diagnostic. scope_kwargs accepts policy,queries,points,pointers,message. Passing checks to ctx.out is unnecessary.
- `ctx.guard('Gxx', bool_or_None)` records an obligation; summaries use conjunction, None for not established. Every owning module must call every assigned guard even on partial data. G01/G02/G14/G15 root; G03/G04 causal; G05..G10 structural; G11..G13 evidence.
- `ctx.tick(n=1)` accounts operations/checks cooperative time; `ctx.node_tick()` accounts one expanded node and one operation. Both raise `ComputationLimit` with `.name` on declared bounds. Loops with exponential work MUST call tick, including joins/preorder checks/certificate enumeration. Limits may be zero and are execution constraints, never hard problem constraints.
- `InputError(code,pointer,message)` reports structural invalidity; `ComputationLimit(name)` reports operational exhaustion. Exceptions are propagated to engine; don't silently catch arbitrary exceptions.

## Module functions

`schema.parse(raw:bytes,limits:dict)->dict` detects UTF8/JSON duplicate keys and strict scalar grammar; `schema.validate(ctx)->None` checks ALL input blocks, exact fields, nominal refs, key uniqueness, times/support, but leaves mathematical component guards to modules. Raises InputError. Query references to causal paths are checked by causal after expansion.

`causal.build_trees(ctx)->dict[policy_id,Tree]`; `causal.validate_queries(ctx,trees)->bool` returns False only for unresolved references, raises InputError for proven invalid ones. Tree is dict `{policy,nodes,node_map,complete,scenario_map,words,causal}`: nodes is list wire Nodes; node_map maps path tuples to those Nodes; complete bool; scenario_map maps scenario IDs to leaf path tuples or None values; use defined(tree["causal"]["scenarios"]) for exact coverage; words maps leaf path tuples to exogenous tuples; causal is exact wire causal object. Query leaves only t=H, no early stopping as leaves. Preserve action=pi(t,i) even if executable/admissible fail.

`structural.evaluate(ctx,trees)->dict[policy_id,dict]` returns exact fields functional,composition,resources,generative,welfare. It may add internal coordination ONLY to ctx.facts, never wire output. `.facts[policy]` stores booleans `functional_data_complete`, `generative_data_complete` for raw individual valuation data before shared calibration/translation guards. `structural.apply_common_guards(ctx,trees,policy_results,b0)->None` checks calibration/translation over union of B0 candidate scopes, blocks all dependent B0 valuations if shared guards fail (no favorable subgroup). B0 determined by root using causal/scenarios + these two raw data flags + complete welfare profile + PVS. Strong G05..G10 check ALL target policies, regardless hard status.

`evidence.evaluate(ctx,trees,structural_results)->dict[policy_id,dict]` returns exact fields evidence,probability,hard. It must preserve genuine partial domains, all zero-mass branches, canonical 0/1 certificates, hard scope Cell + known_scope. No decision/frontier or selector here. Node completeness determines whether scope is known; negative hard witnesses may still refute incomplete scopes. G11 checks legitimacy/derivation of partial evaluator, NOT universal definedness of V.

Root engine merges causal+structural+evidence per policy; applies common guard operation; decision generates B,C,feasibility,pairs,frontier,coverage,selection and G14/G15. EXHAUSTIVE uses G01–G15 before selection; integration additionally checks correct selection or correct absence. On LIMIT minimal Result with BLOCKED decision/integration is permitted. On structural INVALID, policies=[], decision/integration BLOCKED.

Verification must recalculate evidence/outputs from immutable input. Merely inspecting PASS tags is forbidden. Dedicated decisive certificate checker must accept valid noncanonical A supersets of Sem (canonical generator uses equality). Sets/table order and generated identifier spelling aren't semantics; causal path/list order is. Independent tests/auditor challenge implementations and cert mutations.
