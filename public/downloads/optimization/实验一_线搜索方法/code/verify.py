"""当前实验的独立数值与结果核验。"""
import json
import math
from pathlib import Path
import unittest
import numpy as np
from main import golden,parabolic
from main import scalar_f,scalar_g,phi,phi_g


class Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((Path(__file__).resolve().parents[1]/'results/results.json').read_text(encoding='utf-8'))

    def test_scalar_derivatives(self):
        for f,g,points in [(scalar_f,scalar_g,[-19.,-2.,-.7,0.,3.,19.]),(phi,phi_g,[-1.7,-.2,.5,1.5])]:
            for x in points:
                with self.subTest(x=x,f=f.__name__):
                    h=1e-5; numerical=(f(x+h)-f(x-h))/(2*h)
                    self.assertAlmostEqual(g(x),numerical,delta=1e-5*max(1,abs(g(x))))

    def test_exp1_accuracy_and_bracket(self):
        a,m,b=self.data['exp1']['bracket']
        self.assertLess(scalar_f(m),scalar_f(a));self.assertLess(scalar_f(m),scalar_f(b))
        for name,r in self.data['exp1']['runs'].items():
            with self.subTest(name=name):self.assertLessEqual(r['abs_error'],1e-6)


    def test_classroom_three_point_interpolation(self):
        # 真实抛物线的三点插值应一次预测到精确驻点（课件公式）。
        f = lambda x: (x-0.37)**2+2.
        x, history = parabolic(f, -2., 3., tol=1e-9)
        self.assertAlmostEqual(x, 0.37, delta=1e-9)
        self.assertIn('x_bar', history[-1])
        self.assertEqual(history[-1].get('stop'), 'abs(x_bar-x2)<tol')

    def test_first_vertex_matches_classroom_formula(self):
        f = lambda x: (x - 0.2)**2 + 0.1 * (x - 0.2)**4
        x1, x2, x3 = -1.0, 0.0, 1.0
        f1, f2, f3 = f(x1), f(x2), f(x3)
        B = ((x2**2 - x3**2)*f1 + (x3**2 - x1**2)*f2
             + (x1**2 - x2**2)*f3)
        C = (x2 - x3)*f1 + (x3 - x1)*f2 + (x1 - x2)*f3
        _, history = parabolic(f, x1, x3, middle=x2)
        self.assertAlmostEqual(history[1]['x_bar'], B / (2*C), delta=1e-12)

    def test_flat_interpolant_is_rejected(self):
        with self.assertRaises(RuntimeError):
            parabolic(lambda x: 1.0, -1.0, 1.0)

    def test_invalid_inputs(self):
        for solve in [golden,parabolic]:
            with self.assertRaises(ValueError):solve(lambda x:x*x,1.,-1.)
            with self.assertRaises(ValueError):solve(lambda x:x*x,-1.,1.,tol=0.)


if __name__=='__main__':unittest.main(verbosity=2)
