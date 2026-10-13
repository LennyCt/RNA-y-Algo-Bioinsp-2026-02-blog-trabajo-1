"""
Registro de problemas de prueba y contador explícito de evaluaciones.

Regla de comparación justa:
  - n_f    : evaluaciones de f
  - n_grad : evaluaciones de grad f
  - Equivalencia: un gradiente por diferencias centrales cuesta 2*n evaluaciones
    de f en dimensión n, así que  equivalent_cost = n_f + 2*n*n_grad.
    (Se usa el gradiente analítico por velocidad, pero se le cobra ese costo
    para que la comparación con los métodos sin gradiente sea justa.)
"""
import numpy as np
from funciones import rosenbrock, rastrigin

A_ROSEN, B_ROSEN = 1.0, 100.0


def grad_rosenbrock(x, a=A_ROSEN, b=B_ROSEN):
    x = np.asarray(x, dtype=float)
    g = np.zeros_like(x)
    r = x[1:] - x[:-1] ** 2
    g[:-1] += -4 * b * x[:-1] * r + 2 * (x[:-1] - a)
    g[1:] += 2 * b * r
    return g


def grad_rastrigin(x):
    x = np.asarray(x, dtype=float)
    return 2 * x + 20 * np.pi * np.sin(2 * np.pi * x)


PROBLEMS = {
    "rosenbrock": dict(f=rosenbrock, grad=grad_rosenbrock,
                       bounds=(-2.048, 2.048), x_opt=1.0, f_opt=0.0),
    "rastrigin": dict(f=rastrigin, grad=grad_rastrigin,
                      bounds=(-5.12, 5.12), x_opt=0.0, f_opt=0.0),
}


class Objective:
    """Envuelve f y grad f y cuenta cada evaluación."""

    def __init__(self, name, dim):
        p = PROBLEMS[name]
        self.name, self.dim = name, dim
        self.lo, self.hi = p["bounds"]
        self.f_opt = p["f_opt"]
        self.x_opt = np.full(dim, p["x_opt"])
        self._f, self._g = p["f"], p["grad"]
        self.n_f = 0
        self.n_grad = 0

    def f(self, x):
        self.n_f += 1
        return float(self._f(np.asarray(x, dtype=float)))

    def f_pop(self, X):
        """X de forma (N, dim). Cuenta N evaluaciones."""
        X = np.atleast_2d(X)
        self.n_f += X.shape[0]
        return np.asarray(self._f(X.T), dtype=float)

    def grad(self, x):
        self.n_grad += 1
        return self._g(x)

    @property
    def equivalent_cost(self):
        return self.n_f + 2 * self.dim * self.n_grad


def check_gradients(dim=3, n=20, seed=0, tol=1e-4):
    """Compara el gradiente analítico con diferencias centrales."""
    rng = np.random.default_rng(seed)
    h = 1e-6
    for name, p in PROBLEMS.items():
        worst = 0.0
        for _ in range(n):
            x = rng.uniform(*p["bounds"], dim)
            numeric = np.array([(p["f"](x + h * e) - p["f"](x - h * e)) / (2 * h)
                            for e in np.eye(dim)])
            analytic = p["grad"](x)
            worst = max(worst, np.max(np.abs(numeric - analytic) / (1 + np.abs(numeric))))
        print(f"{name:11s} dim={dim}: error relativo máx = {worst:.2e}",
              "OK" if worst < tol else "FALLA")
