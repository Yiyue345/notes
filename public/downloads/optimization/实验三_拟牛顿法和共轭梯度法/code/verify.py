"""当前实验的独立数值与结果核验。"""
import json
from pathlib import Path
import unittest
import numpy as np
from scipy.optimize import minimize
from main import f4,g4,h4,f5,g5,h5


class Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((Path(__file__).resolve().parents[1]/'results/results.json').read_text(encoding='utf-8'))

    def test_vector_derivatives(self):
        for f,g,H,points in [(f4,g4,h4,[[1.,.7],[1.,2.]]),
                             (f5,g5,h5,[[0.,0.,0.],[.3,.8,1.1]])]:
            for z in points:
                x=np.array(z);n=len(x);step=1e-5
                gn=np.array([(f(x+step*e)-f(x-step*e))/(2*step) for e in np.eye(n)])
                Hn=np.column_stack([(g(x+step*e)-g(x-step*e))/(2*step) for e in np.eye(n)])
                np.testing.assert_allclose(g(x),gn,atol=2e-7,rtol=1e-5)
                np.testing.assert_allclose(H(x),Hn,atol=2e-7,rtol=1e-4)

    def test_quasi_newton_and_cg(self):
        for name,r in self.data['exp3'].items():
            with self.subTest(name=name):
                self.assertLessEqual(r['grad_norm'],1e-6)
                ref=np.ones(3) if name.startswith('V_') else np.zeros(2)
                np.testing.assert_allclose(r['x'],ref,atol=4e-6)
                fun,grad=(f5,g5) if len(ref)==3 else (f4,g4)
                start=[0.,0.,0.] if len(ref)==3 else ([1.,.7] if '_a_' in name else [1.,2.])
                independent=minimize(fun,start,jac=grad,method='BFGS',options={'gtol':1e-8})
                self.assertLess(abs(independent.fun-r['f']),1e-9)
                vals=[h['f'] for h in r['history']]
                self.assertTrue(all(b<=a+1e-12 for a,b in zip(vals,vals[1:])))

if __name__=='__main__':unittest.main(verbosity=2)
