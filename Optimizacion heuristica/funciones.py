
import numpy as np


# Funcion de Rosenbrock
def rosenbrock(x, a=1, b=100):
    """
    x: vector de entrada de dimension d.
    """
    x = np.asarray(x, dtype=float)
    return np.sum(
        b * (x[1:] - x[:-1]**2)**2
        + (x[:-1] - a)**2,
        axis=0
    )


# Funcion de Rastrigin
def rastrigin(x):
    """
    x: vector de entrada de dimension d.
    """
    x = np.asarray(x, dtype=float)
    d = x.shape[0]

    return 10 * d + np.sum(
        x**2 - 10 * np.cos(2 * np.pi * x),
        axis=0
    )


# Funcion de Schwefel
def schwefel(x):
    """
    x: vector de entrada de dimension d.
    """
    x = np.asarray(x, dtype=float)
    d = x.shape[0]

    return 418.9829 * d - np.sum(
        x * np.sin(np.sqrt(np.abs(x))),
        axis=0
    )


# Funcion de Griewank
def griewank(x):
    """
    x: vector (d,) o arreglo de forma (d, n, m).
    La primera dimension corresponde a las variables.
    """
    x = np.asarray(x, dtype=float)
    d = x.shape[0]

    # Adapta los indices a la cantidad de dimensiones del arreglo
    forma = (d,) + (1,) * (x.ndim - 1)
    indices = np.sqrt(np.arange(1, d + 1)).reshape(forma)

    term1 = np.sum(x**2, axis=0) / 4000
    term2 = np.prod(np.cos(x / indices), axis=0)

    return 1 + term1 - term2


# Funcion Goldstein-Price (solo 2 variables)
def goldstein_price(x):
    """
    x: vector [x1, x2].
    """
    x = np.asarray(x, dtype=float)
    x1, x2 = x[0], x[1]

    term1 = 1 + (x1 + x2 + 1)**2 * (
        19 - 14*x1 + 3*x1**2
        - 14*x2 + 6*x1*x2 + 3*x2**2
    )

    term2 = 30 + (2*x1 - 3*x2)**2 * (
        18 - 32*x1 + 12*x1**2
        + 48*x2 - 36*x1*x2 + 27*x2**2
    )

    return term1 * term2


# Funcion de las seis jorobas de camello (solo 2 variables)
def camel_six_humps(x):
    """
    x: vector [x1, x2].
    """
    x = np.asarray(x, dtype=float)
    x1, x2 = x[0], x[1]

    term1 = (4 - 2.1*x1**2 + x1**4 / 3) * x1**2
    term2 = x1 * x2
    term3 = (-4 + 4*x2**2) * x2**2

    return term1 + term2 + term3


x2 = np.array([1.0, 1.0])
x3 = np.array([1.0, 1.0, 1.0])

print("Rosenbrock 2D:", rosenbrock(x2))
print("Rastrigin 2D:", rastrigin(x2))
print("Schwefel 2D:", schwefel(x2))
print("Griewank 2D:", griewank(x2))

print("Goldstein-Price:", goldstein_price(x2))
print("Seis jorobas de camello:", camel_six_humps(x2))

print("Rosenbrock 3D:", rosenbrock(x3))
print("Rastrigin 3D:", rastrigin(x3))
print("Schwefel 3D:", schwefel(x3))
print("Griewank 3D:", griewank(x3))