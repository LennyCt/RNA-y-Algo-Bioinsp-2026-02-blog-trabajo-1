"""Algoritmo genético de codificación real.

Selección por torneo de tamaño k, cruce BLX-alfa, mutación gaussiana por gen
y elitismo. Minimiza f.

  BLX-alfa: hijo_j ~ U[min(a_j,b_j) - alfa*d_j, max(a_j,b_j) + alfa*d_j],  d_j=|a_j-b_j|
  Mutación: x_j <- x_j + N(0, (sigma*(hi-lo))^2)  con prob. prob_mut por gen
"""
import numpy as np


def genetic_algorithm(obj, rng, pop_size=50, crossover_prob=0.9, mutation_prob=None,
                       mutation_sigma=0.1, blx_alpha=0.5, tournament_k=3, elitism=2,
                       budget=10000, record=False):
    N, d = pop_size, obj.dim
    mutation_prob = 1.0 / d if mutation_prob is None else mutation_prob
    span = obj.hi - obj.lo

    pop = rng.uniform(obj.lo, obj.hi, (N, d))
    fit = obj.f_pop(pop)
    gen = 0
    curve = [(obj.equivalent_cost, fit.min())]
    traj = []

    def save_frame(g):
        if record and d == 2:
            traj.extend(dict(generation=g, x1=p[0], x2=p[1], **{"f(x1,x2)": v})
                        for p, v in zip(pop, fit))
    save_frame(0)

    while obj.n_f + N <= budget:
        # Selección por torneo
        candidates = rng.integers(0, N, (N, tournament_k))
        winners = candidates[np.arange(N), np.argmin(fit[candidates], axis=1)]
        parent_a = pop[winners]
        parent_b = pop[winners[rng.permutation(N)]]

        # Cruce BLX-alfa (solo a una fracción prob_cruce de los pares)
        min_vals, max_vals = np.minimum(parent_a, parent_b), np.maximum(parent_a, parent_b)
        diff = max_vals - min_vals
        children = rng.uniform(min_vals - blx_alpha * diff, max_vals + blx_alpha * diff)
        no_crossover = rng.random(N) >= crossover_prob
        children[no_crossover] = parent_a[no_crossover]

        # Mutación gaussiana
        mask = rng.random((N, d)) < mutation_prob
        children += mask * rng.normal(0.0, mutation_sigma * span, (N, d))
        children = np.clip(children, obj.lo, obj.hi)

        child_fit = obj.f_pop(children)

        # Elitismo: los mejores padres reemplazan a los peores hijos
        if elitism > 0:
            elite_idx = np.argsort(fit)[:elitism]
            worst_idx = np.argsort(child_fit)[-elitism:]
            children[worst_idx], child_fit[worst_idx] = pop[elite_idx], fit[elite_idx]

        pop, fit = children, child_fit
        gen += 1
        curve.append((obj.equivalent_cost, fit.min()))
        save_frame(gen)

    i = int(np.argmin(fit))
    return dict(best_x=pop[i].copy(), best_f=float(fit[i]), curve=curve,
                trajectory=traj if record and d == 2 else None)
