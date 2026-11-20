"""Independent numerical checks for the worked examples in 01--07."""

from fractions import Fraction as F

import numpy as np


def close(actual, expected, tol=1e-10):
    if not np.allclose(actual, expected, atol=tol, rtol=tol):
        raise AssertionError(f"actual={actual}, expected={expected}")


def exact_equal(actual, expected):
    if actual != expected:
        raise AssertionError(f"actual={actual}, expected={expected}")


def verify_foundations_and_taylor():
    Q = np.array([[2.0, 2.0], [2.0, 6.0]])
    x = np.array([1.0, 2.0])
    close(Q @ x, [6, 14])
    close([np.array([1.0, 0.0]) @ Q @ np.array([1.0, 0.0]),
           np.array([0.0, 1.0]) @ Q @ np.array([0.0, 1.0])], [2, 6])
    if np.linalg.det(Q) <= 0 or Q[0, 0] <= 0:
        raise AssertionError("worked Hessian should be positive definite")

    x = np.array([1.0, 1.0]); h = np.array([0.1, -0.2])
    Q = np.diag([2.0, 4.0]); g = np.array([2.0, 4.0])
    taylor = 3 + g @ h + 0.5 * h @ Q @ h
    direct = (x[0] + h[0])**2 + 2*(x[1] + h[1])**2
    close(taylor, 2.49); close(direct, 2.49)


def pivot(A, b, basis, row, col):
    A = [r[:] for r in A]; b = b[:]; basis = basis[:]
    p = A[row][col]
    A[row] = [v / p for v in A[row]]; b[row] /= p
    for i in range(len(A)):
        if i == row:
            continue
        factor = A[i][col]
        A[i] = [v - factor*w for v, w in zip(A[i], A[row])]
        b[i] -= factor*b[row]
    basis[row] = col
    return A, b, basis


def reduced_costs(A, c, basis):
    return [c[j] - sum(c[basis[i]]*A[i][j] for i in range(len(A)))
            for j in range(len(c))]


def verify_simplex_tables():
    # 02 two-variable teaching example.
    A = [[F(1),F(1),F(1),F(0)], [F(2),F(1),F(0),F(1)]]
    b = [F(4),F(6)]; c = [F(-3),F(-2),F(0),F(0)]; basis = [2,3]
    A,b,basis = pivot(A,b,basis,1,0)
    exact_equal(A, [[F(0),F(1,2),F(1),F(-1,2)],
                    [F(1),F(1,2),F(0),F(1,2)]])
    exact_equal(b, [F(1),F(3)])
    exact_equal(reduced_costs(A,c,basis), [F(0),F(-1,2),F(0),F(3,2)])
    A,b,basis = pivot(A,b,basis,0,1)
    exact_equal(b, [F(2),F(2)])
    exact_equal(reduced_costs(A,c,basis), [F(0),F(0),F(1),F(1)])
    exact_equal(sum(c[basis[i]]*b[i] for i in range(2)), F(-10))

    # A-exam tableau, including both pivots.
    A = [[F(2),F(3),F(1),F(0),F(0)],
         [F(4),F(-3),F(0),F(1),F(0)],
         [F(3),F(-1),F(0),F(0),F(1)]]
    b = [F(10),F(8),F(9)]; c = [F(-5),F(-3),F(0),F(0),F(0)]; basis=[2,3,4]
    A,b,basis = pivot(A,b,basis,1,0)
    A,b,basis = pivot(A,b,basis,0,1)
    expected = [[F(0),F(1),F(2,9),F(-1,9),F(0)],
                [F(1),F(0),F(1,6),F(1,6),F(0)],
                [F(0),F(0),F(-5,18),F(-11,18),F(1)]]
    exact_equal(A, expected); exact_equal(b, [F(4,3),F(3),F(4,3)])
    exact_equal(reduced_costs(A,c,basis), [F(0),F(0),F(3,2),F(1,2),F(0)])
    exact_equal(sum(c[basis[i]]*b[i] for i in range(3)), F(-19))

    # Teacher assignment tableau.
    A = [[F(2),F(-1),F(2),F(1),F(0),F(0)],
         [F(-5),F(3),F(0),F(0),F(1),F(0)],
         [F(2),F(0),F(7),F(0),F(0),F(1)]]
    b=[F(7),F(15),F(10)]; c=[F(3),F(-5),F(6),F(0),F(0),F(0)]; basis=[3,4,5]
    A,b,basis=pivot(A,b,basis,1,1)
    A,b,basis=pivot(A,b,basis,2,0)
    expected=[[F(0),F(0),F(5,6),F(1),F(1,3),F(-1,6)],
              [F(0),F(1),F(35,6),F(0),F(1,3),F(5,6)],
              [F(1),F(0),F(7,2),F(0),F(0),F(1,2)]]
    exact_equal(A,expected); exact_equal(b,[F(31,3),F(40,3),F(5)])
    exact_equal(reduced_costs(A,c,basis),[F(0),F(0),F(74,3),F(0),F(5,3),F(8,3)])
    exact_equal(sum(c[basis[i]]*b[i] for i in range(3)),F(-155,3))


def verify_line_search_examples():
    alpha = F(2,3)
    exact_equal(F(3)-8*alpha+6*alpha*alpha, F(1,3))
    rho = (np.sqrt(5)-1)/2
    p, q = (1-rho)*6, rho*6
    close([p,q], [2.2917960675,3.7082039325])
    # Classroom three-point formula for points 0,1,3.
    xs=[F(0),F(1),F(3)]; fs=[F(13,4),F(5,4),F(13,4)]
    B=(xs[1]**2-xs[2]**2)*fs[0]+(xs[2]**2-xs[0]**2)*fs[1]+(xs[0]**2-xs[1]**2)*fs[2]
    C=(xs[1]-xs[2])*fs[0]+(xs[2]-xs[0])*fs[1]+(xs[0]-xs[1])*fs[2]
    exact_equal(B/(2*C), F(3,2))
    # Armijo/Wolfe values for f(t)=t^2, t=2, d=-4.
    def phi(a): return (2-4*a)**2
    def dphi(a): return -16+32*a
    if not phi(F(1,16)) <= F(4)-F(8,5)*F(1,16):
        raise AssertionError("small step should pass Armijo")
    if not dphi(F(1,16)) < F(-8):
        raise AssertionError("small step should fail Wolfe")


def verify_common_quadratic():
    Q = np.diag([1.0, 2.0]); x0 = np.array([2.0, 1.0])
    g0 = Q @ x0; d0 = -g0
    a0 = -(g0 @ d0)/(d0 @ Q @ d0)
    x1 = x0 + a0*d0
    close(a0, 2/3); close(x1, [2/3, -1/3])
    d_newton = np.linalg.solve(Q, -g0)
    close(x0 + d_newton, [0, 0])
    g1 = Q @ x1
    beta = (g1 @ g1)/(g0 @ g0)
    d1 = -g1 + beta*d0
    a1 = -(g1 @ d1)/(d1 @ Q @ d1)
    close(beta, 1/9); close(a1, 3/4); close(x1 + a1*d1, [0, 0])


def verify_exam():
    Q = np.array([[1.0, 2.0], [2.0, 6.0]])
    g0 = np.array([-3.0, 0.0])
    close(np.array([2.0, -1.0]) + np.linalg.solve(Q, -g0), [11, -4])

    Q = np.array([[4.0, -2.0], [-2.0, 2.0]])
    x0 = np.array([1.0, 3.0]); c = np.array([-3.0, 1.0])
    g0 = Q @ x0 + c; d0 = -g0
    a0 = -(g0 @ d0)/(d0 @ Q @ d0); x1 = x0 + a0*d0
    g1 = Q @ x1 + c; beta = (g1 @ g1)/(g0 @ g0)
    d1 = -g1 + beta*d0; a1 = -(g1 @ d1)/(d1 @ Q @ d1)
    close(x1, [2, 2]); close(x1 + a1*d1, [1, .5])


def verify_teacher_iterative_examples():
    Q=np.array([[6.,0.,-2.],[0.,2.,0.],[-2.,0.,1.]])
    c=np.array([0.,1.,0.]); x0=np.array([1.,0.,3.])
    g0=Q@x0+c; d0=-g0; alpha=-(g0@d0)/(d0@Q@d0)
    close(g0,[0,1,1]); close(alpha,2/3); close(x0+alpha*d0,[1,-2/3,7/3])

    Q=np.array([[3.,2.,0.],[2.,2.,1.],[0.,1.,6.]])
    g0=np.array([6.,9.,4.]); x0=np.array([1.,2.,0.])
    close(x0+np.linalg.solve(Q,-g0),[43/9,-20/3,7/9])

    Q=np.array([[3.,2.,2.],[2.,2.,1.],[2.,1.,6.]])
    c=np.array([-2.,2.,0.]); x=np.zeros(3); g=Q@x+c; d=-g
    a=-(g@d)/(d@Q@d); x1=x+a*d; g1=Q@x1+c
    beta=(g1@g1)/(g@g); d1=-g1+beta*d; a1=-(g1@d1)/(d1@Q@d1)
    close(a,2); close(x1,[4,-4,0]); close(beta,3)
    close(a1,1/6); close(x1+a1*d1,[14/3,-16/3,-2/3])


def verify_active_set_example():
    x_star = np.array([F(5, 4), F(1, 4)], dtype=object)
    target = np.array([F(2), F(1)], dtype=object)
    diff = x_star - target
    value = F(1, 2) * sum(v*v for v in diff)
    if value != F(9, 16):
        raise AssertionError(value)
    if sum(x_star) != F(3, 2):
        raise AssertionError(x_star)
    g = x_star - target
    close(np.array(g,dtype=float), .75*np.array([-1.,-1.]))


def verify_bilinear_interpolation():
    top=F(4,5)*200+F(1,5)*180
    bottom=F(4,5)*210+F(1,5)*190
    value=F(7,10)*top+F(3,10)*bottom
    exact_equal((top,bottom,value),(F(196),F(206),F(199)))


if __name__ == "__main__":
    verify_foundations_and_taylor()
    verify_simplex_tables()
    verify_line_search_examples()
    verify_common_quadratic()
    verify_exam()
    verify_teacher_iterative_examples()
    verify_active_set_example()
    verify_bilinear_interpolation()
    print("all selected worked-example checks passed")
