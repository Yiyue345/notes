"""当前实验的独立数值与结果核验。"""
import json
import math
from pathlib import Path
import unittest
import numpy as np
from main import Q1,Q2,C12,f3,g3,h3,quadratic


class Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((Path(__file__).resolve().parents[1]/'results/results.json').read_text(encoding='utf-8'))

    def test_vector_derivatives(self):
        for f,g,H,points in [(f3,g3,h3,[[-3.5,.5],[-10.,10.],[-3.,0.]])]:
            for z in points:
                x=np.array(z);n=len(x);step=1e-5
                gn=np.array([(f(x+step*e)-f(x-step*e))/(2*step) for e in np.eye(n)])
                Hn=np.column_stack([(g(x+step*e)-g(x-step*e))/(2*step) for e in np.eye(n)])
                np.testing.assert_allclose(g(x),gn,atol=2e-7,rtol=1e-5)
                np.testing.assert_allclose(H(x),Hn,atol=2e-7,rtol=1e-4)

    def test_quadratic_exact_solutions(self):
        for name,Q in [('I',Q1),('II',Q2)]:
            self.assertGreater(np.min(np.linalg.eigvalsh(Q)),0)
            ref=np.linalg.solve(Q,-C12)
            for method in ['sd','newton']:
                r=self.data['exp2'][f'{name}_{method}']
                self.assertLessEqual(r['grad_norm'],1e-6)
                np.testing.assert_allclose(r['x'],ref,atol=4e-6)
            self.assertEqual(self.data['exp2'][f'{name}_newton']['iterations'],1)

    def test_problem_III_outcomes(self):
        for key in ['III_far_sd','III_near_sd','III_near_newton']:
            r=self.data['exp2'][key]
            self.assertLessEqual(r['grad_norm'],1e-6)
            self.assertLess(abs(r['f']-math.log(2)),1e-10)
        far=self.data['exp2']['III_far_newton']
        self.assertLessEqual(far['grad_norm'],1e-6)
        self.assertGreater(far['f']-math.log(2),.3)
        self.assertLess(min(far['hessian_eigenvalues']),0)
        # F(t)=1+t+exp(t)-2^(1+t), F''>0,F'(0)>0,F(0)=0 证明全局最优。
        self.assertGreater(1-2*math.log(2)**2,0)
        self.assertGreater(2-2*math.log(2),0)

if __name__=='__main__':unittest.main(verbosity=2)
