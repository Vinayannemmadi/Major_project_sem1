"""Cluster-maintenance policies.

All policies share the same local maintenance (rejoin after a link break, local
formation among unaffiliated vehicles, merging of adjacent CHs). They differ in
WHEN and HOW the cluster head is changed:

  periodic   - HARNES-style BC election, full re-clustering every period_s.
  eager      - HARNES-style 'highest BC is CH', re-evaluated every step, switch
               as soon as any member has higher BC (no hysteresis, no cost check).
  costaware  - OURS: evaluate a cluster only when its predicted hazard (expected
               member link breaks within tau) makes a switch potentially worth its
               cost (hazard * c_event > gamma * (|C|+1)) and the CH has served dwell_s;
               then run cluster-local BC, score candidates with the composite
               stability score, and switch only if hysteresis + (benefit > gamma * cost)
               both hold.

Control-message model (counted, not simulated at packet level):
  JOIN            1 per member (re)affiliation
  CH_ADV          1 per new/handed-over cluster
  controller sync 1 per handover (CH -> LEC update)
  full re-cluster 2N (N state reports up, N assignments down)
Beacons are identical for every policy and are reported separately.
"""
import time

import numpy as np

from .clustering import bc_scores, composite_scores, greedy_form


class Ctx:
    """Per-step view of the network handed to a policy."""
    def __init__(self, t, D, S, L, R, theta):
        self.t = t
        self.S = S
        self.L = L
        self.N = D.shape[0]
        eye = np.eye(self.N, dtype=bool)
        self.adj = (D <= R) & ~eye
        self.join_adj = self.adj & (S >= theta)


class Base:
    name = "base"

    def __init__(self, N, cfg, dt):
        self.N = N
        self.cfg = cfg
        self.dt = dt
        self.lam = cfg["bc_lambda"]
        self.head = -np.ones(N, dtype=int)
        self.ch_start = np.full(N, -1.0)
        self.prev_is_ch = np.zeros(N, dtype=bool)
        self.prev_head = self.head.copy()
        self.ch_adj_cnt = np.zeros((N, N), dtype=int)
        self.merge_steps = max(1, int(round(cfg["common"]["merge_s"] / dt)))
        self.m = dict(control_msgs=0, ch_elections=0, handovers=0, full_reclusters=0,
                      merges=0, bc_calls=0, bc_nodes=0, forced_rejoins=0, affil_switches=0,
                      cpu_s=0.0, tenures=[], iso_sum=0.0, clusters_sum=0.0,
                      size_sum=0.0, steps=0)

    # ---------- helpers ----------
    def counts(self):
        h = self.head[self.head >= 0]
        return np.bincount(h, minlength=self.N)

    def normalize(self):
        """A 'CH' with no members is just an unaffiliated vehicle."""
        cnt = self.counts()
        for v in range(self.N):
            if self.head[v] == v and cnt[v] < 2:
                self.head[v] = -1

    def chs(self):
        cnt = self.counts()
        return [v for v in range(self.N) if self.head[v] == v and cnt[v] >= 2]

    def msg(self, n):
        self.m["control_msgs"] += n

    def bc_all(self, ctx):
        self.m["bc_calls"] += 1
        self.m["bc_nodes"] += self.N
        return bc_scores(np.arange(self.N), ctx.adj, ctx.S, self.lam)

    # ---------- shared maintenance ----------
    def rejoin_pending(self, ctx):
        chs = set(self.chs())
        for v in range(self.N):
            if self.head[v] == -1:
                cand = [c for c in chs if ctx.join_adj[v, c]]
                if cand:
                    self.head[v] = max(cand, key=lambda c: ctx.S[v, c])
                    self.msg(1)

    def local_score(self, nodes, ctx):
        return bc_scores(nodes, ctx.adj, ctx.S, self.lam)

    def local_repair(self, ctx):
        h = self.head
        for v in range(self.N):
            c = h[v]
            if c >= 0 and c != v and ((not ctx.adj[v, c]) or h[c] != c):
                h[v] = -1
                self.m["forced_rejoins"] += 1
        self.normalize()
        self.rejoin_pending(ctx)
        iso = np.array([v for v in range(self.N) if h[v] == -1], dtype=int)
        if len(iso) >= 2 and ctx.join_adj[np.ix_(iso, iso)].any():
            self.m["bc_nodes"] += len(iso)
            sc = self.local_score(iso, ctx)
            asg = greedy_form(iso, sc, ctx.join_adj)
            for v, c in asg.items():
                h[v] = c
            for c in set(asg.values()):
                size = sum(1 for v in asg if asg[v] == c)
                self.msg(1 + (size - 1))     # CH_ADV + JOINs
        self.merge(ctx)

    def merge(self, ctx):
        chs = self.chs()
        is_ch = np.zeros(self.N, dtype=bool)
        is_ch[chs] = True
        both = np.outer(is_ch, is_ch) & ctx.adj
        self.ch_adj_cnt[both] += 1
        self.ch_adj_cnt[~both] = 0
        cnt = self.counts()
        done = set()
        for a in chs:
            for b in chs:
                if a < b and a not in done and b not in done and \
                        self.ch_adj_cnt[a, b] >= self.merge_steps:
                    loser, winner = (a, b) if (cnt[a], -a) < (cnt[b], -b) else (b, a)
                    for v in np.where(self.head == loser)[0]:
                        self.head[v] = -1
                    self.ch_adj_cnt[loser, :] = 0
                    self.ch_adj_cnt[:, loser] = 0
                    self.m["merges"] += 1
                    done.update((a, b))
        if done:
            self.normalize()
            self.rejoin_pending(ctx)

    def handover(self, c, b, ctx):
        members = np.where(self.head == c)[0]
        for v in members:
            if v == b:
                self.head[b] = b
            elif ctx.join_adj[v, b]:
                self.head[v] = b
                self.msg(1)
            else:
                self.head[v] = -1
        self.msg(2)                          # CH_ADV + controller sync
        self.m["handovers"] += 1

    def full_recluster(self, ctx, first=False):
        bc = self.bc_all(ctx)
        score = self.global_score(bc, ctx)
        asg = greedy_form(np.arange(self.N), score, ctx.join_adj)
        newh = -np.ones(self.N, dtype=int)
        for v, c in asg.items():
            newh[v] = c
        self.head = newh
        self.normalize()
        if not first:
            self.msg(2 * self.N)
            self.m["full_reclusters"] += 1

    def global_score(self, bc, ctx):
        return bc

    # ---------- bookkeeping (not timed) ----------
    def update_roles(self, t, count):
        cnt = self.counts()
        is_ch = np.array([self.head[v] == v and cnt[v] >= 2 for v in range(self.N)])
        new = is_ch & ~self.prev_is_ch
        ended = self.prev_is_ch & ~is_ch
        if count:
            self.m["ch_elections"] += int(new.sum())
            for v in np.where(ended)[0]:
                self.m["tenures"].append(t - self.ch_start[v])
            idx = np.arange(self.N)
            sw = (self.head != self.prev_head) & (self.head >= 0) & (self.prev_head >= 0) \
                & (self.head != idx) & (self.prev_head != idx)
            self.m["affil_switches"] += int(sw.sum())
            self.m["iso_sum"] += float((self.head < 0).mean())
            self.m["clusters_sum"] += float(is_ch.sum())
            self.m["size_sum"] += float(cnt[is_ch].mean()) if is_ch.any() else 0.0
            self.m["steps"] += 1
        self.ch_start[new] = t
        self.prev_is_ch = is_ch
        self.prev_head = self.head.copy()

    def finish(self, t_end):
        for v in np.where(self.prev_is_ch)[0]:
            self.m["tenures"].append(t_end - self.ch_start[v])   # censored at end of run

    # ---------- main entry ----------
    def initial(self, ctx):
        self.full_recluster(ctx, first=True)
        self.update_roles(ctx.t, count=False)

    def step(self, ctx):
        raise NotImplementedError

    def timed_step(self, ctx):
        t0 = time.process_time()
        self.step(ctx)
        self.m["cpu_s"] += time.process_time() - t0
        self.update_roles(ctx.t, count=True)


class Periodic(Base):
    name = "periodic"

    def __init__(self, N, cfg, dt, override=None):
        super().__init__(N, cfg, dt)
        p = dict(cfg["policies"]["periodic"])
        if override:
            p.update(override)
        self.period = max(1, int(round(p["period_s"] / dt)))

    def step(self, ctx):
        self.local_repair(ctx)
        if ctx.t % self.period == 0:
            self.full_recluster(ctx)


class Eager(Base):
    name = "eager"

    def step(self, ctx):
        self.local_repair(ctx)
        bc = self.bc_all(ctx)
        for c in self.chs():
            members = np.where(self.head == c)[0]
            b = members[np.argmax(bc[members])]
            if b != c and bc[b] > bc[c] + 1e-12:
                self.handover(c, b, ctx)
        self.normalize()
        self.rejoin_pending(ctx)


class CostAware(Base):
    name = "costaware"

    def __init__(self, N, cfg, dt, override=None):
        super().__init__(N, cfg, dt)
        self.p = dict(cfg["policies"]["costaware"])
        if override:
            self.p.update(override)
        self.w = self.p["weights"]
        self.last_global = -1e9
        self.Lmax = cfg["l_max_s"]
        self.tau = cfg["horizon_tau_s"]

    # composite score used for formation and local formation
    def global_score(self, bc, ctx):
        mx = bc.max() if bc.max() > 0 else 1.0
        return composite_scores(np.arange(self.N), ctx.join_adj, ctx.S, ctx.L,
                                bc / mx, self.w, self.Lmax)

    def local_score(self, nodes, ctx):
        bc = bc_scores(nodes, ctx.adj, ctx.S, self.lam)
        mx = bc.max() if bc.max() > 0 else 1.0
        return composite_scores(nodes, ctx.join_adj, ctx.S, ctx.L, bc / mx, self.w, self.Lmax)

    def hazard_sum(self, v, others, ctx):
        """Expected number of member-link breaks within the horizon if v is CH."""
        if len(others) == 0:
            return 0.0
        s = np.clip(ctx.S[v, others], 1e-3, 1.0)
        return float((-np.log(s)).sum())

    def step(self, ctx):
        self.local_repair(ctx)
        p = self.p
        t = ctx.t
        dwell = p["dwell_s"] / self.dt

        # 0) predictive member re-affiliation: leave a CH whose predicted survival is
        #    very low for a clearly better CH in range (1 JOIN instead of a link break)
        leave = p.get("proactive_leave", 0.0)
        if leave > 0:
            chs_now = self.chs()
            for v in range(self.N):
                c = self.head[v]
                if c >= 0 and c != v and ctx.S[v, c] < leave:
                    cand = [u for u in chs_now if u != c and ctx.join_adj[v, u]]
                    if cand:
                        u = max(cand, key=lambda u: ctx.S[v, u])
                        if ctx.S[v, u] > ctx.S[v, c]:
                            self.head[v] = u
                            self.msg(1)
            self.normalize()

        # 1) global trigger: too many vehicles unaffiliated although they have neighbours
        has_nb = ctx.join_adj.any(axis=1)
        iso_frac = float(((self.head < 0) & has_nb).mean())
        if iso_frac > p["global_isolated_frac"] and \
                (t - self.last_global) * self.dt >= p["global_min_gap_s"]:
            self.full_recluster(ctx)
            self.last_global = t
            return

        # 2) predictive trigger (cheap: uses the survival matrix only)
        # Necessary condition for any switch to pay off: even a perfect new CH (zero
        # expected breaks) can save at most hazard(c) * c_event messages, so evaluate
        # (and pay for BC) only if that upper bound exceeds the switching cost.
        triggered = []
        for c in self.chs():
            others = np.where((self.head == c) & (np.arange(self.N) != c))[0]
            cost_c = len(others) + 2
            upper = self.hazard_sum(c, others, ctx) * p["c_event"]
            if upper > p["gamma"] * cost_c and t - self.ch_start[c] >= dwell:
                triggered.append(c)
        if not triggered:
            return

        # 3) only now pay for betweenness centrality -- and only on the triggered
        #    cluster's neighbourhood (members + their 1-hop neighbours), which is
        #    what the zone controller needs for a cluster-local decision.
        for c in triggered:
            members = np.where(self.head == c)[0]
            if len(members) < 2:
                continue
            nodes = np.where(ctx.adj[members].any(axis=0) | np.isin(np.arange(self.N), members))[0]
            self.m["bc_calls"] += 1
            self.m["bc_nodes"] += len(nodes)
            bc_loc = bc_scores(nodes, ctx.adj, ctx.S, self.lam)
            mx = bc_loc.max() if bc_loc.max() > 0 else 1.0
            pos_in = {int(v): i for i, v in enumerate(nodes)}
            bc_m = np.array([bc_loc[pos_in[int(v)]] for v in members]) / mx
            mask = np.zeros((self.N, self.N), dtype=bool)
            mask[np.ix_(members, members)] = True
            sc = composite_scores(members, mask, ctx.S, ctx.L, bc_m, self.w, self.Lmax)
            ic = int(np.where(members == c)[0][0])
            ib = int(np.argmax(sc))
            b = int(members[ib])
            if b == c or sc[ib] - sc[ic] <= p["hysteresis"]:
                continue
            others_c = members[members != c]
            others_b = members[members != b]
            benefit = (self.hazard_sum(c, others_c, ctx) - self.hazard_sum(b, others_b, ctx)) \
                * p["c_event"]
            cost = len(members) + 1          # (|C|-1) JOINs + CH_ADV + controller sync
            if benefit > p["gamma"] * cost:
                self.handover(c, b, ctx)
        self.normalize()
        self.rejoin_pending(ctx)


def make_policy(name, N, cfg, dt, override=None):
    if name.startswith("periodic"):
        return Periodic(N, cfg, dt, override)
    if name == "eager":
        return Eager(N, cfg, dt)
    if name.startswith("costaware"):
        return CostAware(N, cfg, dt, override)
    raise ValueError(name)
