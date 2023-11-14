from functools import reduce
import numpy as np
from scipy import linalg
from scipy import integrate

class Ci:
    def CountCi(self, I, n, s):
        self.matrix_ci = np.zeros((n, n * (s + 1)))
        for _ in range(n):
            self.matrix_ci[_][I * n + _] = 1
        return self.matrix_ci
    def ReturnCi(self):
        return self.matrix_ci

# return F, Psi, H, R, x0, u
class IMFVariablesSaver:
    # modes: IMF, IMF_test, dIMF, dIMF_test
    def Variables(self, tetta, N, modeName, modeTest):
        # return: F, dF, Psi, dPsi, H, dH, R, dR, x0, dx0, u
        if modeName == "IMF" and modeTest == 2:
            self.F = np.array([-0.8, 1., tetta[0], 0.])
            self.dF = [np.array([0., 0., 1., 0.]), np.array([0., 0., 0., 0.])]
            self.Psi = np.array([tetta[1], 1.])
            self.dPsi = [np.array([0., 0.]), np.array([1., 0.])]
            self.H = np.array([1., 0.])
            self.dH = [np.array([0., 0.]), np.array([0., 0.])]
            self.R = 0.1
            self.dR = [0., 0.]
            self.x0 = np.array([[0.], [0.]])
            self.dx0 = [np.array([[0.], [0.]]), np.array([[0.], [0.]])]
            self.u = np.array([[1.] for i in range(N)])
            return self.F, self.dF, self.Psi, self.dPsi, self.H, self.dH, self.R, self.dR, self.x0, self.dx0, self.u
        elif modeName == "IMF" and modeTest == 1:
            self.F = np.array([[0.]])
            self.dF = [np.array([[0.]]), np.array([[0.]])]
            self.Psi = np.array([[tetta[0], tetta[1]]])
            self.dPsi = [np.array([[1., 0.]]), np.array([[0., 1.]])]
            self.H = np.array([1.])
            self.dH = [np.array([0.]), np.array([0.])]
            self.R = 0.3
            self.dR = [0., 0.]
            self.x0 = np.zeros((1, 1))
            self.dx0 = [np.zeros((1, 1)) for i in range(2)]
            self.u = np.array([[[1.], [1.]] for i in range(N + 1)])
            return self.F, self.dF, self.Psi, self.dPsi, self.H, self.dH, self.R, self.dR, self.x0, self.dx0, self.u

class TransisionMatrix:
    rP = [0, 0, 0, 0]
    @staticmethod
    def CountMatrix(t0, t1, F, rParam):
        a = (F).reshape((rParam[0], rParam[1]))
        eMatrix = linalg.expm(np.array(F).reshape(rParam[0], rParam[1]) * (t1 - t0))
        return eMatrix
    @staticmethod
    def CountMatrixdF(t0, t1, F, dF, rParam):
        eMatrix = np.dot(linalg.expm(np.array(F).reshape(rParam[0], rParam[1]) * (t1 - t0)),
                              np.array(dF).reshape(rParam[0], rParam[1]) * (t1 - t0))
        return eMatrix
class IntegrateMethods:
    u = np.array([[]])
    @staticmethod
    def A0(x, t1, F, Psi, u, index, eMatrix):
        b0 = np.array(Psi).reshape(eMatrix.rP[2], eMatrix.rP[3])
        b_0 = u[index]
        b1 = np.dot(np.array(Psi).reshape(eMatrix.rP[2], eMatrix.rP[3]), u[index])
        b2 = eMatrix.CountMatrix(x, t1, F, eMatrix.rP)
        b3 = np.dot(b2, b0)
        b4 = np.dot(b3, u[index])
        a0 = reduce(np.dot, [eMatrix.CountMatrix(x, t1, F, eMatrix.rP),
                    np.array(Psi).reshape(eMatrix.rP[2], eMatrix.rP[3]), u[index]])
        return a0
    @staticmethod
    def A1(x, t1, F, dF, Psi, dPsi, u, index, eMatrix):

        a1 = reduce(np.dot, [eMatrix.CountMatrixdF(x, t1, F, dF, eMatrix.rP),
                             np.array(Psi).reshape(eMatrix.rP[2], eMatrix.rP[3]), u[index]]) + \
             reduce(np.dot, [eMatrix.CountMatrix(x, t1, F, eMatrix.rP),
                             np.array(dPsi).reshape(eMatrix.rP[2], eMatrix.rP[3]), u[index]])

        return a1
class Xatk:
    def __init__(self, F, dF, Psi, dPsi, t, x0, dx0):
        self.F = F
        self.dF = dF
        self.Psi = Psi
        self.dPsi = dPsi
        self.x0 = x0
        self.dx0 = dx0
        self.t = t

    def StartCountXatk(self, index, eMatrix, iMartix):
        u = np.array(iMartix.u)
        a0 = integrate.quad_vec(iMartix.A0, self.t[0], self.t[1],
                                args=(self.t[1], self.F, self.Psi, u, index, eMatrix))[0]

        a1 = integrate.quad_vec(iMartix.A1, self.t[0], self.t[1],
                                args=(self.t[1], (self.F), (self.dF[0]),
                                self.Psi, self.dPsi[0], u, index, eMatrix))[0]

        a2 = integrate.quad_vec(iMartix.A1, self.t[0], self.t[1],
                                args=(self.t[1], self.F, self.dF[1],
                                self.Psi, self.dPsi[1], u, index, eMatrix))[0]
        xat0 = np.hstack((a0, a1, a2))
        return xat0
    def ContinueCountXatk(self, fatk, atk, xatk):
        return np.dot(fatk, xatk) + atk

class dXatk:
    def __init__(self, F, dF, Psi, dPsi, t, x0, dx0):
        self.F = F
        self.dF = dF
        self.Psi = Psi
        self.dPsi = dPsi
        self.x0 = x0
        self.dx0 = dx0
        self.t = t

    def StartCountXatk(self, datk):
        dXt0du = datk
        return dXt0du
    def ContinueCountXatk(self, fatk, datk, dxatk):
        return np.dot(fatk, dxatk) + datk

class Fatk:
    def __init__(self, F, dF):
        self.F = F
        self.dF = dF
    def CountFatk(self, t, eMatrix):
        O = np.zeros((eMatrix.rP[0], eMatrix.rP[1]))
        a1 = np.hstack((eMatrix.CountMatrix(t[0], t[1], self.F, eMatrix.rP), O, O))

        a2 = np.hstack((eMatrix.CountMatrixdF(t[0], t[1], self.F, self.dF[0], eMatrix.rP),
                        eMatrix.CountMatrix(t[0], t[1], self.F, eMatrix.rP), O))

        a3 = np.hstack((eMatrix.CountMatrixdF(t[0], t[1], self.F, self.dF[1], eMatrix.rP), O,
                        eMatrix.CountMatrix(t[0], t[1], self.F, eMatrix.rP)))
        self.faMatrix = np.vstack((a1, a2, a3))
        return self.faMatrix
    def ReturnFatk(self):
        return self.faMatrix

class Atk:
    def __init__(self, F, dF, Psi, dPsi, x0, dx0):
        self.F = F
        self.dF = dF
        self.Psi = Psi
        self.dPsi = dPsi
        self.x0 = x0
        self.dx0 = dx0
    def CountAtk(self, t, index, eMatrix, iMatrix):
        u = iMatrix.u
        a0 = integrate.quad_vec(iMatrix.A0, t[0], t[1], args=(t[1], self.F, self.Psi, u, index, eMatrix))[0]

        a1 = integrate.quad_vec(iMatrix.A1, t[0], t[1],
                            args=(t[1], self.F, self.dF[0], self.Psi, self.dPsi[0], u, index, eMatrix))[0]

        a2 = integrate.quad_vec(iMatrix.A1, t[0], t[1],
                                args=(t[1], self.F, self.dF[1],self.Psi, self.dPsi[1], u, index, eMatrix))[0]

        self.atk = np.vstack((a0, a1, a2))
        return self.atk

    def ReturnAtk(self):
        return self.atk

class dAtk:
    def __init__(self, F, dF, Psi, dPsi, x0, dx0, N):
        self.F = F
        self.dF = dF
        self.Psi = Psi
        self.dPsi = dPsi
        self.x0 = x0
        self.dx0 = dx0
        self.N = N
    def CountAtk(self, t, n, k, betta, alpha, eMatrix, iMatrix):
        u, index = [1.], 0
        if n == 1:
            dudua = np.zeros((self.N, 1))
        else:
            dudua = 1.

        if (betta == k) and (n == 1):
            dudua[alpha] = 1.

        a0 = np.dot(integrate.quad_vec(iMatrix.A0, t[0], t[1], args=(t[1], self.F, self.Psi, u, index, eMatrix))[0], dudua)

        a1 = np.dot(integrate.quad_vec(iMatrix.A1, t[0], t[1],
                            args=(t[1], self.F, self.dF[0], self.Psi, self.dPsi[0], u, index, eMatrix))[0], dudua)

        a2 = np.dot(integrate.quad_vec(iMatrix.A1, t[0], t[1],
                                args=(t[1], self.F, self.dF[1],self.Psi, self.dPsi[1], u, index, eMatrix))[0], dudua)

        self.datk = np.vstack((a0, a1, a2))
        return self.datk

    def ReturnAtk(self):
        return self.datk




def dMatrixOfFisher(n ,s, H, dH, R, cObject, xatk, dxatk):
    delta_M = np.array([[0., 0.], [0., 0.]])
    coeff_dxa_tk_plus_one = np.dot(dxatk, xatk.transpose()) + np.dot(xatk, dxatk.transpose())
    for i in range(2):
        for j in range(2):
            A0 = reduce(np.dot, [dH[i], cObject.CountCi(I=0, n=n, s=s),
                                 coeff_dxa_tk_plus_one,
                                 cObject.CountCi(I=0, n=n, s=s).transpose(), dH[j].transpose(), pow(R, -1)])

            A1 = reduce(np.dot, [dH[i], cObject.CountCi(I=0, n=n, s=s),
                                 coeff_dxa_tk_plus_one,
                                 cObject.CountCi(I=j + 1, n=n, s=s).transpose(), H.transpose(), pow(R, -1)])

            A2 = reduce(np.dot, [H, cObject.CountCi(I=i + 1, n=n, s=s),
                                 coeff_dxa_tk_plus_one,
                                 cObject.CountCi(I=0, n=n, s=s).transpose(), dH[j].transpose(), pow(R, -1)])

            A3 = reduce(np.dot, [H, cObject.CountCi(I=i + 1, n=n, s=s),
                                 coeff_dxa_tk_plus_one,
                                 cObject.CountCi(I=j + 1, n=n, s=s).transpose(), H.transpose(), pow(R, -1)])

            delta_M[i][j] = A0 + A1 + A2 + A3
    return delta_M

def dIMF(params, cObject, xAObject, dxAObject, FaObject, AtkObject, dAtkObject, eMatrix, iMatrix):
    n = params['n']
    t = params['t']
    s = params['s']
    N = params['N']
    r = params['r']
    H = params['H']
    dH = params['dH']
    R = params['R']
    dmFisher = np.zeros((N, r, 2, 2))
    datk, dxatk = [], np.zeros((N, r, N, 3 * n, 1))  # shape: N, alpha, betta
    for k in range(N):
        if k == 0:
            xatk = xAObject.StartCountXatk(k, eMatrix, iMatrix).reshape(3*n, 1)
            for betta in range(N):
                for alpha in range(r):
                    datk.append(dAtkObject.CountAtk(t=[t[0], t[1]], n=n, k=k, betta=betta, alpha=alpha, eMatrix=eMatrix, iMatrix=iMatrix))
                    dxatk[k][alpha][betta] = dxAObject.StartCountXatk(datk[alpha])
                    dmFisher[k][alpha] += dMatrixOfFisher(n, s, H, dH, R, cObject, xatk, dxatk[k][alpha][betta])
                datk.clear()
            continue

        fatk = FaObject.CountFatk(t=[t[k], t[k + 1]], eMatrix=eMatrix)
        atk = AtkObject.CountAtk(t=[t[k], t[k + 1]], index=k, eMatrix=eMatrix, iMatrix=iMatrix).reshape(3*n,1)
        xatk = xAObject.ContinueCountXatk(fatk, atk, xatk)

        for betta in range(N):
            for alpha in range(r):
                datk.append(dAtkObject.CountAtk(t=[t[k], t[k + 1]], n=n, k=k, betta=betta, alpha=alpha, eMatrix=eMatrix, iMatrix=iMatrix))
                dxatk[k][alpha][betta] = (dxAObject.ContinueCountXatk(fatk, datk[alpha], dxatk[k - 1][alpha][betta]))
                dmFisher[k][alpha] += dMatrixOfFisher(n, s, H, dH, R, cObject, xatk, dxatk[k][alpha][betta])
            datk.clear()

    return dmFisher

def main():
    # Определение переменных
    m = q = v = nu = 1
    r = 1 # Размерность вектора управления
    n = 2 # Размерность вектора х0
    s = 2 # Количество производных по тетта
    N = 20 # Число испытаний
    tetta_true = np.array([-1.5, 1.0])
    tetta_false = np.array([-1., 1.])
    t = []

    if n == 1:
        count = 0
        param = [1, 1, 1, 2] # Reshape params for test
        for i in range(N + 1):
            if i == 0:
                t.append(count)
            else:
                count += 0.5
                t.append(count)
    else:
        param = [2, 2, 2, 1] # F (2, 2) and Psi (2, 1)
        t = np.arange(N + 1)

    varObject = IMFVariablesSaver()

    # Choose Test or NoTest
    F, dF, Psi, dPsi, H, dH, R, dR, x0, dx0, u = varObject.Variables(tetta_false, N, "IMF", modeTest=n)
    params = {"F": F, "dF": dF, "Psi": Psi, "dPsi": dPsi, "H": H, "dH": dH, "R": R,
              "dR": dR, "x0": x0, "dx0": dx0, "N": N, "n": n, "t": t, "s": s, "r": r}
    eMatrix = TransisionMatrix()
    eMatrix.rP = param
    iMatrix = IntegrateMethods()
    iMatrix.u = u
    xAObject = Xatk(F, dF, Psi, dPsi, t=[t[0], t[1]], x0=x0, dx0=dx0)
    dxAObject = dXatk(F, dF, Psi, dPsi, t=[t[0], t[1]], x0=x0, dx0=dx0)
    FaObject = Fatk(F, dF)
    AtkObject = Atk(F, dF, Psi, dPsi, x0=x0, dx0=dx0)
    dAtkObject = dAtk(F, dF, Psi, dPsi, x0=x0, dx0=dx0, N=N)
    cObject = Ci()

    print(dIMF(params, cObject, xAObject, dxAObject, FaObject, AtkObject, dAtkObject, eMatrix, iMatrix))



    a = 0

main()