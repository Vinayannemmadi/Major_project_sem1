"""Predictive link model (our extension of the paper's Gaussian link-reliability idea).

Paper: D_l = T_R / delta_v, with delta_v ~ Normal(mu, sigma), reliability = integral of g(T).
Ours:  predict the pair distance tau seconds ahead with constant relative velocity,
       d_hat(tau) = |dp + dv * tau|.  Because distance is convex in time, a link that is
       inside range now and at tau is inside range for the whole interval, so
           S_ij(tau) = P(link survives tau) = Phi((R - d_hat) / sigma_p)
       where sigma_p is the std of the prediction error, estimated online from the
       errors the predictor actually made tau seconds ago (sigma_p ~ sigma_dv * tau).
Also provides the exact kinematic lifetime L_ij (time until |dp + dv t| = R).
"""
import numpy as np
from scipy.special import ndtr


def pair_arrays(pos_t, vel_t, R, tau, Lmax):
    """One time step: current distance D, predicted distance D_hat at tau, and
    kinematic remaining lifetime L for every vehicle pair."""
    N = pos_t.shape[0]
    dp = pos_t[None, :, :] - pos_t[:, None, :]
    dv = vel_t[None, :, :] - vel_t[:, None, :]
    D = np.linalg.norm(dp, axis=2)
    Dhat = np.linalg.norm(dp + dv * tau, axis=2)
    a = (dv ** 2).sum(2)
    b = 2 * (dp * dv).sum(2)
    c = (dp ** 2).sum(2) - R * R
    L = np.full((N, N), float(Lmax))
    disc = b * b - 4 * a * c
    ok = (a > 1e-9) & (disc >= 0)
    root = np.zeros_like(a)
    root[ok] = (-b[ok] + np.sqrt(disc[ok])) / (2 * a[ok])
    L[ok] = np.clip(root[ok], 0, Lmax)
    L[c > 0] = 0.0
    return D, Dhat, L


def precompute(pos, vel, cfg, dt):
    """Offline version (whole trace at once). OnlineLinkModel below gives the same
    numbers step by step for the live SUMO demo."""
    R = cfg["radio_range_m"]
    tau = cfg["horizon_tau_s"]
    k = max(1, int(round(tau / dt)))
    Lmax = cfg["l_max_s"]
    T, N, _ = pos.shape
    D = np.empty((T, N, N))
    Dhat = np.empty((T, N, N))
    L = np.empty((T, N, N))
    for t in range(T):
        D[t], Dhat[t], L[t] = pair_arrays(pos[t], vel[t], R, tau, Lmax)
    eye = np.eye(N, dtype=bool)

    # online estimate of prediction-error std (causal: uses only errors already observed)
    ss = np.zeros(T)
    cnt = np.zeros(T)
    for t in range(k, T):
        m = (D[t - k] <= R) & ~eye
        e = D[t] - Dhat[t - k]
        ss[t] = (e[m] ** 2).sum()
        cnt[t] = m.sum()
    W = max(1, int(round(cfg["sigma_window_s"] / dt)))
    sigma = np.full(T, float(cfg["sigma_init_m"]))
    for t in range(T):
        lo = max(0, t - W + 1)
        c = cnt[lo:t + 1].sum()
        if c >= 30:
            sigma[t] = max(cfg["sigma_floor_m"], np.sqrt(ss[lo:t + 1].sum() / c))

    S = ndtr((R - Dhat) / sigma[:, None, None])
    S[(D > R) | eye[None]] = 0.0
    return {"D": D, "S": S, "L": L, "sigma": sigma, "k": k, "N": N, "T": T}


class OnlineLinkModel:
    """Step-by-step link model for live use (SUMO + TraCI). Feed the current positions
    and velocities each step; returns D, S, L for that step. Uses only the past, exactly
    like precompute() (sigma from errors the predictor made tau seconds ago)."""

    def __init__(self, N, cfg, dt):
        self.R = cfg["radio_range_m"]
        self.tau = cfg["horizon_tau_s"]
        self.k = max(1, int(round(self.tau / dt)))
        self.Lmax = cfg["l_max_s"]
        self.W = max(1, int(round(cfg["sigma_window_s"] / dt)))
        self.init = float(cfg["sigma_init_m"])
        self.floor = cfg["sigma_floor_m"]
        self.eye = np.eye(N, dtype=bool)
        self.hist = []        # last k+1 (D, Dhat)
        self.errs = []        # last W (sum of squared errors, count)
        self.sigma = self.init

    def update(self, pos_t, vel_t):
        D, Dhat, L = pair_arrays(pos_t, vel_t, self.R, self.tau, self.Lmax)
        self.hist.append((D, Dhat))
        if len(self.hist) > self.k + 1:
            self.hist.pop(0)
        if len(self.hist) == self.k + 1:
            D_old, Dhat_old = self.hist[0]
            m = (D_old <= self.R) & ~self.eye
            e = D - Dhat_old
            self.errs.append(((e[m] ** 2).sum(), m.sum()))
        else:
            self.errs.append((0.0, 0))
        if len(self.errs) > self.W:
            self.errs.pop(0)
        c = sum(x[1] for x in self.errs)
        self.sigma = max(self.floor, np.sqrt(sum(x[0] for x in self.errs) / c)) if c >= 30 else self.init
        S = ndtr((self.R - Dhat) / self.sigma)
        S[(D > self.R) | self.eye] = 0.0
        return D, S, L


def prediction_quality(pre, cfg):
    """How good are the survival predictions? Compare S_ij(tau) made at time t
    with whether the link really stayed in range for the whole next tau seconds."""
    R = cfg["radio_range_m"]
    D, S, L, k = pre["D"], pre["S"], pre["L"], pre["k"]
    T, N = pre["T"], pre["N"]
    eye = np.eye(N, dtype=bool)
    P, Y, Lk = [], [], []
    for t in range(T - k):
        m = (D[t] <= R) & ~eye
        if not m.any():
            continue
        alive = (D[t:t + k + 1] <= R).all(axis=0)
        P.append(S[t][m])
        Y.append(alive[m].astype(float))
        Lk.append((L[t][m] >= cfg["horizon_tau_s"]).astype(float))
    if not P:
        return {}
    P, Y, Lk = np.concatenate(P), np.concatenate(Y), np.concatenate(Lk)
    base = Y.mean()
    return {
        "pairs_evaluated": int(len(Y)),
        "survival_rate": float(base),
        "brier_prob_model": float(np.mean((P - Y) ** 2)),
        "brier_constant_rate": float(np.mean((base - Y) ** 2)),
        "acc_prob_model@0.5": float(np.mean((P >= 0.5) == (Y == 1))),
        "acc_kinematic@tau": float(np.mean(Lk == Y)),
    }
