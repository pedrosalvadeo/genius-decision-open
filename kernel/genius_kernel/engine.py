"""End-to-end FP1 orchestration. All user mathematics comes from frozen bytes."""
from .common import (Context, InputError, ComputationLimit, SPECIFICATION,
                     defined, validate_limits)


def _result(ctx, status, presentation, policies, decision, integration):
    return {"format": "genius-fp1-result/1.0", "input_digest": ctx.digest,
            "specification": SPECIFICATION, "execution": ctx.execution(status),
            "presentation": presentation, "diagnostics": ctx.diagnostics,
            "checks": ctx.checks, "policies": policies,
            "decision": decision, "integration": integration}


def evaluate(raw, limits=None):
    """Evaluate an exact UTF-8 byte string. Operational limits are not input axioms."""
    from . import schema, causal, structural, evidence, decision as decide
    if not isinstance(raw, bytes):
        raise TypeError("evaluate requires the original UTF-8 bytes, not a reserialized object")
    limits = validate_limits(limits)
    ctx = Context({}, raw, limits)
    presentation = "UNRESOLVED"
    try:
        ctx.tick()
        ctx.data = schema.parse(raw, limits)
        schema.validate(ctx)
        ctx.H = int(ctx.data["meta"]["horizon"])
        ctx.check("INPUT_TYPES", "PASS")
        ctx.guard("G02", True)
        trees = causal.build_trees(ctx)
        references_resolved = causal.validate_queries(ctx, trees)
        presentation = "VALID" if references_resolved else "UNRESOLVED"
        ctx.guard("G01", True if references_resolved else None)
        sr = structural.evaluate(ctx, trees)
        er = evidence.evaluate(ctx, trees, sr)
        results = {pid: {"policy": pid, "causal": trees[pid]["causal"],
                         **sr[pid], **er[pid]} for pid in sorted(trees)}
        b0 = [pid for pid in sorted(trees) if trees[pid]["complete"]
              and defined(trees[pid]["causal"]["scenarios"])
              and ctx.facts.get(pid, {}).get("functional_data_complete", False)
              and ctx.facts.get(pid, {}).get("generative_data_complete", False)
              and defined(results[pid]["welfare"]["profile"])
              and defined(results[pid]["probability"]["pvs"])]
        structural.apply_common_guards(ctx, trees, results, b0)
        result_decision, integration = decide.evaluate(ctx, trees, results)
        ctx.completed_policies = set(results)
        return _result(ctx, "COMPLETE", presentation, list(results.values()),
                       result_decision, integration)
    except InputError as exc:
        # A diagnostic refers to the containing input when the missing key itself
        # cannot be resolved. The exact offending path remains in its message.
        ctx.diag(exc.code, "INPUT", message=f"{exc.pointer}: {exc.message}")
        ctx.check("INPUT_TYPES", "FAIL", detail=f"{exc.code}: {exc.pointer}")
        ctx.completed_policies.clear()
        decision = ctx.block("DEPENDENCY_BLOCKED", "DECISION",
                             message="The input presentation is structurally invalid.")
        integration = ctx.block("DEPENDENCY_BLOCKED", "DECISION")
        return _result(ctx, "COMPLETE", "INVALID", [], decision, integration)
    except ComputationLimit as exc:
        ctx.completed_policies.clear()
        decision = ctx.block("COMPUTATION_LIMIT", "EXECUTION", message=exc.name)
        integration = ctx.block("COMPUTATION_LIMIT", "EXECUTION", message=exc.name)
        return _result(ctx, "LIMITED", presentation, [], decision, integration)
    except RecursionError:
        ctx.completed_policies.clear()
        decision = ctx.block("COMPUTATION_LIMIT", "EXECUTION", message="python_recursion_depth")
        integration = ctx.block("COMPUTATION_LIMIT", "EXECUTION", message="python_recursion_depth")
        return _result(ctx, "LIMITED", presentation, [], decision, integration)
    except Exception as exc:
        ctx.completed_policies.clear()
        decision = ctx.block("INTERNAL_ERROR", "EXECUTION",
                             message=f"{type(exc).__name__}: {exc}")
        integration = ctx.block("INTERNAL_ERROR", "EXECUTION")
        return _result(ctx, "ERROR", presentation, [], decision, integration)
