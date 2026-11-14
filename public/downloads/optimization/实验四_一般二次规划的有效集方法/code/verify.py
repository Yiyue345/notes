"""当前实验的独立数值与结果核验。"""
import json
import itertools
from pathlib import Path
import unittest
import numpy as np
from scipy.optimize import minimize
from main import active_set
from main import QP


class Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((Path(__file__).resolve().parents[1]/'results/results.json').read_text(encoding='utf-8'))

    def test_qp_independent_enumeration_and_slsqp(self):
        for name,(Q,c,c0,A,b,x0) in QP.items():
            r=self.data['exp4'][name];x=np.array(r['x'])
            for residual in r['kkt'].values():self.assertLessEqual(residual,1e-6)
            for row in r['history']:self.assertGreaterEqual(np.min(A@np.array(row['x'])-b),-1e-6)
            candidates=[];n=len(x)
            for size in range(n+1):
                for subset in itertools.combinations(range(len(b)),size):
                    AW=A[list(subset)];bw=b[list(subset)]
                    K=np.block([[Q,-AW.T],[AW,np.zeros((size,size))]])
                    try:sol=np.linalg.solve(K,np.r_[-c,bw])
                    except np.linalg.LinAlgError:continue
                    z,lam=sol[:n],sol[n:]
                    if np.min(A@z-b)>=-1e-8 and (not size or np.min(lam)>=-1e-8):
                        candidates.append((.5*z@Q@z+c@z+c0,z))
            self.assertTrue(candidates)
            ref=min(candidates,key=lambda pair:pair[0])[1]
            np.testing.assert_allclose(x,ref,atol=1e-8)
            opt=minimize(lambda z:.5*z@Q@z+c@z+c0,x0,jac=lambda z:Q@z+c,
                         constraints={'type':'ineq','fun':lambda z:A@z-b,'jac':lambda z:A},
                         method='SLSQP',options={'ftol':1e-12})
            self.assertTrue(opt.success,opt.message)
            np.testing.assert_allclose(x,opt.x,atol=1e-6)

    def test_invalid_inputs(self):
        Q,c,_,A,b,_=QP['VI']
        with self.assertRaises(ValueError):active_set(Q,c,A,b,[100.,100.])



    def test_classroom_example_7_2(self):
        """11月6日 PPT 第170-180张：有效集法例7.2，初始点(2,0)。"""
        # min (x1-1)^2 + (x2-2.5)^2
        # s.t. x1-2*x2+2 >=0, -x1-2*x2+6>=0,
        #      -x1+2*x2+2>=0, x1>=0, x2>=0
        Q = 2*np.eye(2)
        c = np.array([-2., -5.])
        A = np.array([[1.,-2.],[-1.,-2.],[-1.,2.],
                      [1.,0.],[0.,1.]])
        b = np.array([-2.,-6.,-2.,0.,0.])
        r = active_set(Q,c,A,b,np.array([2.,0.]),tol=1e-9)
        x = np.array(r['x'])
        self.assertLessEqual(r['kkt']['stationarity'],1e-8)
        self.assertLessEqual(r['kkt']['primal'],1e-8)
        self.assertLessEqual(r['kkt']['dual'],1e-8)
        self.assertLessEqual(r['kkt']['complementarity'],1e-8)
        np.testing.assert_allclose(x, [1.4,1.7], atol=1e-8)

if __name__=='__main__':unittest.main(verbosity=2)
