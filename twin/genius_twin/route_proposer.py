"""Module VII, learned proposer: a small neural network that learns where better routes are.

The network reads a route in the twin's own language (which action applies at
each step, unconditionally or under each declared condition) and predicts what
the kernel will say about it in every scenario: whether the life condition
holds, each carrier's welfare at every step, and each function's terminal value:
the same coordinates the kernel's per-carrier comparison uses. It is trained only on kernel verdict rows of the same model.

It never judges. Its predictions only choose which variations are sent to the
kernel; every route it proposes is evaluated and verified like any other, and
champions change only by the kernel's per-carrier comparison. Floats are used
for the predictions because they are proposals, not results.

Choice, per carrier (Pedro, 2026-10-18: life condition first, then the best
route for each carrier): among candidates predicted to keep the life condition
wherever the champion keeps it, the one predicted to beat the carrier's
champion on every one of its coordinates, else the one whose worst predicted
margin is largest (a max-min, never a sum). One slot always goes to a random
candidate, so the network keeps seeing routes it would not pick.
"""
import math
import random
from fractions import Fraction

FORMAT = "genius-route-proposer/1"


def _resolve(policy, step):
    """The action the route takes at a step whatever the state, and the conditional rules met before it."""
    conditional = []
    for rule in policy["rules"]:
        if step not in rule["steps"]:
            continue
        if not rule["when"]:
            return rule["action"], conditional
        conditional.append(rule)
    return policy["default_action"], conditional


class Encoding:
    """Feature and target spaces of one model; nothing domain-specific."""

    def __init__(self, model, values):
        self.H = model["horizon"]
        self.actions = [a["id"] for a in model["actions"]]
        self.conditions = [(s, op, v) for s in sorted(values) for v in values[s] for op in ("ge", "le")] + [None]
        self.scenarios = [s["id"] for s in model["scenarios"]]
        self.welfare = [(f"{w['carrier']}.{w['dimension']}", 1 if w["direction"] == "higher" else -1) for w in model["welfare"]]
        self.functions = [f["id"] for f in model.get("functions", [])]
        A, C = len(self.actions), len(self.conditions)
        self.size = self.H * A * (1 + C)
        self.targets = []
        for sid in self.scenarios:
            self.targets.append(("life", sid, None))
            for key, _ in self.welfare:
                self.targets += [("path", sid, (key, t)) for t in range(self.H + 1)]
            self.targets += [("function", sid, f) for f in self.functions]
        self.index = {t: i for i, t in enumerate(self.targets)}

    def features(self, policy):
        """Sparse 0/1-count features: {index: count}."""
        A, C = len(self.actions), len(self.conditions)
        out = {}
        for t in range(1, self.H + 1):
            action, conditional = _resolve(policy, t)
            base = (t - 1) * A
            out[base + self.actions.index(action)] = 1
            for rule in conditional:
                a = self.actions.index(rule["action"])
                for p in rule["when"]:
                    key = (p["stock"], p["op"], p["value"]) if p["kind"] == "stock" else None
                    c = self.conditions.index(key) if key in self.conditions else C - 1
                    i = self.H * A + (base + a) * C + c
                    out[i] = out.get(i, 0) + 1
        return out

    def target(self, row):
        """Oriented targets from a verdict row (higher is better for every welfare coordinate)."""
        sign = dict(self.welfare)
        y = []
        for kind, sid, key in self.targets:
            cell = row["by_scenario"][sid]
            if kind == "life":
                y.append({"success": 1.0, "failure": 0.0}.get(cell["task_status"], 0.5))
            elif kind == "path":
                y.append(sign[key[0]] * float(Fraction(cell["welfare_path"][key[0]][key[1]])))
            else:
                y.append(float(Fraction(cell["functions_terminal"][key])))
        return y


class Network:
    """One hidden tanh layer, sparse input, trained with Adam on mean squared error of standardized targets."""

    def __init__(self, inputs, outputs, hidden=16, seed=0):
        rng = random.Random(seed)
        s1, s2 = 1 / math.sqrt(8), 1 / math.sqrt(hidden)
        self.W1 = [[rng.gauss(0, s1) for _ in range(hidden)] for _ in range(inputs)]
        self.b1 = [0.0] * hidden
        self.W2 = [[rng.gauss(0, s2) for _ in range(outputs)] for _ in range(hidden)]
        self.b2 = [0.0] * outputs
        self.hidden, self.outputs = hidden, outputs
        self.mean, self.scale, self.varies = [0.0] * outputs, [1.0] * outputs, [True] * outputs

    def _forward(self, x):
        z = list(self.b1)
        for i, v in x.items():
            row = self.W1[i]
            for j in range(self.hidden):
                z[j] += row[j] * v
        h = [math.tanh(v) for v in z]
        out = list(self.b2)
        for j, hj in enumerate(h):
            row = self.W2[j]
            for k in range(self.outputs):
                out[k] += row[k] * hj
        return h, out

    def predict(self, x):
        _, out = self._forward(x)
        return [o * s + m for o, s, m in zip(out, self.scale, self.mean)]

    def fit(self, xs, ys, epochs=150, lr=0.02, seed=0):
        n = len(ys)
        self.mean = [sum(col) / n for col in zip(*ys)]
        spread = [math.sqrt(sum((v - m) ** 2 for v in col) / n) for col, m in zip(zip(*ys), self.mean)]
        self.varies = [s > 1e-12 for s in spread]
        self.scale = [s if s > 1e-12 else 1.0 for s in spread]
        zs = [[(v - m) / s for v, m, s in zip(y, self.mean, self.scale)] for y in ys]
        params = [self.W1, [self.b1], self.W2, [self.b2]]
        m1 = [[[0.0] * len(r) for r in p] for p in params]
        m2 = [[[0.0] * len(r) for r in p] for p in params]
        rng, order, step = random.Random(seed), list(range(n)), 0
        b1, b2, eps = 0.9, 0.999, 1e-8
        def update(pi, r, c, g):
            m1[pi][r][c] = b1 * m1[pi][r][c] + (1 - b1) * g
            m2[pi][r][c] = b2 * m2[pi][r][c] + (1 - b2) * g * g
            hat1, hat2 = m1[pi][r][c] / (1 - b1 ** step), m2[pi][r][c] / (1 - b2 ** step)
            params[pi][r][c] -= lr * hat1 / (math.sqrt(hat2) + eps)
        for _ in range(epochs):
            rng.shuffle(order)
            for idx in order:
                step += 1
                x, z = xs[idx], zs[idx]
                h, out = self._forward(x)
                d_out = [2 * (o - t) / self.outputs for o, t in zip(out, z)]
                d_h = [sum(self.W2[j][k] * d_out[k] for k in range(self.outputs)) * (1 - h[j] ** 2)
                       for j in range(self.hidden)]
                for j in range(self.hidden):
                    for k in range(self.outputs):
                        update(2, j, k, d_out[k] * h[j])
                for k in range(self.outputs):
                    update(3, 0, k, d_out[k])
                for i, v in x.items():
                    for j in range(self.hidden):
                        update(0, i, j, d_h[j] * v)
                for j in range(self.hidden):
                    update(1, 0, j, d_h[j])
        return self


class LearnedProposer:
    """Chooses which candidate variations the kernel evaluates, from a network trained on verdict rows."""

    def __init__(self, model, values, seed=0, hidden=16, epochs=150, training_rows=()):
        self.model, self.seed, self.hidden, self.epochs = model, seed, hidden, epochs
        self.encoding = Encoding(model, values)
        self.rng = random.Random(seed)
        self.prior = list(training_rows)
        self.history = []

    def _carrier_coords(self, carrier):
        e = self.encoding
        serves = {f["id"] for f in self.model.get("functions", []) if carrier in f["serves"]}
        return [e.index[t] for t in e.targets
                if (t[0] == "path" and t[2][0].split(".")[0] == carrier) or (t[0] == "function" and t[2] in serves)]

    def train(self, rows):
        data = self.prior + list(rows)
        xs = [self.encoding.features(r["policy"]) for r in data]
        ys = [self.encoding.target(r) for r in data]
        net = Network(self.encoding.size, len(self.encoding.targets), self.hidden, self.seed)
        # About the same number of updates whatever the amount of data.
        self.net = net.fit(xs, ys, max(10, min(self.epochs, 9000 // max(1, len(data)))), seed=self.seed)
        # Held-in fit, reported so a reader can see how well the network has learned the verdicts so far.
        life = [self.encoding.index[("life", sid, None)] for sid in self.encoding.scenarios]
        agree = sum(all((net.predict(x)[i] >= 0.5) == (y[i] >= 0.5) for i in life) for x, y in zip(xs, ys))
        return {"rows": len(data), "life_agreement": f"{agree}/{len(data)}"}

    def choose(self, candidates, champions, actual, k):
        """Pick k candidate indices; champions {carrier: route}, actual {route: target vector from its verdict}."""
        e = self.encoding
        life = [e.index[("life", sid, None)] for sid in e.scenarios]
        preds = [self.net.predict(e.features(c)) for c in candidates]
        chosen, notes = [], []
        for carrier, route in sorted(champions.items()):
            if len(chosen) >= k - 1:
                break
            ref = actual[route]
            coords = self._carrier_coords(carrier)
            if not coords:
                continue
            keep = [i for i, p in enumerate(preds) if i not in chosen
                    and all(p[j] >= 0.5 for j in life if ref[j] >= 0.5)]
            if not keep:
                continue
            # Coordinates no verdict has ever seen change cannot separate routes.
            coords = [j for j in coords if self.net.varies[j]] or coords
            spread = self.net.scale
            margin = {i: min((preds[i][j] - ref[j]) / spread[j] for j in coords) for i in keep}
            best = max(keep, key=lambda i: (margin[i], -i))
            chosen.append(best)
            notes.append({"carrier": carrier, "against": route, "predicted_worst_margin": round(margin[best], 3),
                          "predicted_better_everywhere": margin[best] > 0})
        rest = [i for i in range(len(candidates)) if i not in chosen]
        while len(chosen) < k and rest:
            chosen.append(rest.pop(self.rng.randrange(len(rest))))
            notes.append({"exploration": True})
        return chosen, notes
