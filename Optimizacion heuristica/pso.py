"""Optimización por enjambre de partículas (PSO), topología global (gbest).

  v <- w*v + c1*r1*(pbest - x) + c2*r2*(gbest - x),   r1,r2 ~ U(0,1) por componente
  x <- clip(x + v)

Por defecto w=0.729, c1=c2=1.49445 (coeficientes de constricción de Clerc-Kennedy).
La velocidad se limita a vmax_frac*(hi-lo).
"""
import numpy as np


def pso(obj, rng, pop_size=30, w=0.729, c1=1.49445, c2=1.49445, vmax_frac=0.2,
        budget=10000, record=False):
    N, d = pop_size, obj.dim
    span = obj.hi - obj.lo
    vmax = vmax_frac * span

    x = rng.uniform(obj.lo, obj.hi, (N, d))
    v = rng.uniform(-vmax, vmax, (N, d))
    fx = obj.f_pop(x)
    pbest, fpbest = x.copy(), fx.copy()
    g = int(np.argmin(fpbest))
    gbest, fgbest = pbest[g].copy(), fpbest[g]

    it = 0
    curve = [(obj.equivalent_cost, fgbest)]
    traj = []

    def save_frame(k):
        if record and d == 2:
            traj.extend(dict(generation=k, x1=p[0], x2=p[1], **{"f(x1,x2)": val})
                        for p, val in zip(x, fx))
    save_frame(0)

    while obj.n_f + N <= budget:
        r1, r2 = rng.random((N, d)), rng.random((N, d))
        v = w * v + c1 * r1 * (pbest - x) + c2 * r2 * (gbest - x)
        v = np.clip(v, -vmax, vmax)
        x = np.clip(x + v, obj.lo, obj.hi)
        fx = obj.f_pop(x)

        improved = fx < fpbest
        pbest[improved], fpbest[improved] = x[improved], fx[improved]
        g = int(np.argmin(fpbest))
        if fpbest[g] < fgbest:
            gbest, fgbest = pbest[g].copy(), fpbest[g]

        it += 1
        curve.append((obj.equivalent_cost, fgbest))
        save_frame(it)

    return dict(best_x=gbest, best_f=float(fgbest), curve=curve,
                trajectory=traj if record and d == 2 else None)
