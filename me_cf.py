import numpy as np
import os, sys
sys.path.append(os.path.dirname(__file__))
from diis_solver import diis_solver
sys.path.pop()
import jk
import xform
import scipy.sparse.linalg as spla


def get_dm(C, nel):
    D = C[:, :nel]
    D = D @ D.T
    return D


def get_JK(is_fitted, g, D):
    if(is_fitted):
        # FINISH LATER
        X = np.einsum("Pls,ls->P", g, D)
        J = np.einsum("mnP,P->mn", np.swapaxes(g, 0, 2), X)
        Z = np.einsum("Pns,ls->Pnl", g, D)
        K = np.einsum('mlP,Pnl->mn', np.swapaxes(g, 0, 2), Z)
        return (J, K)
    else:
        #J = np.einsum("pqrs,rs->pq", g, D)
        #K = np.einsum("prqs,rs->pq", g, D)
        J, K = jk.getJK_np_Dshift(g, D - np.diag(np.diag(D) * 0.5))
        return (J, K)


def get_fock(H, g, D, opt, F_prev_list, r_prev_list):
    opt = opt.upper()
    # not accelerated
    if(opt == 'NONE' or len(F_prev_list) <= 1):
        J, K = get_JK(len(g.shape) == 3, g, D)
        return H + 2 * J - K
    # DIIS
    elif(opt == 'DIIS'):
        c = diis_solver(r_prev_list) # GET THE COEFFICIENTS!!
        out = 0 * H
        for i, element in enumerate(F_prev_list):
            out += c[i] * element
        return out


def diag(F, A):
    Fp = A.T @ F @ A
    eps, Cp = np.linalg.eigh(Fp)
    C = A @ Cp
    return eps, C


def get_SCF_err(S, D, F):
    return (np.sum(np.abs(S @ D @ F - F @ D @ S)), (S @ D @ F - F @ D @ S))


def xform_2(H, A):
    """
    Basis xform for 2-tensor
    """
    if len(H.shape) != 2:
        raise Exception("Dimension error: arg1 should be a matrix")

    return A.T @ H @ A


def xform_4(g, A):
    """
    Basis xform for 4-tensor
    """
    if len(g.shape) != 4:
        raise Exception("""
            Dimension error: arg1 should be a four-tensor.
            Note that you should set is_fitted to be False.
        """)
    '''
    g = np.einsum('pqrs,pt->tqrs',g,A)    
    g = np.einsum('pqrs,qt->ptrs',g,A)    
    g = np.einsum('pqrs,rt->pqts',g,A)    
    g = np.einsum('pqrs,st->pqrt',g,A)    
    return g
    '''    
    #return np.einsum("ip, jq, pqrs, rk, sl -> ijkl", A, A, g, A, A, optimize=True)
    return xform.xform_4_np(g, A)


def make_f_mo(g, kappa, F, nocc, nbas):
    """
    Make F_ia^kappa in MO basis
    """

    

    # Slices - with RHF reference, nelec = 2 * nocc
    occ = slice(0,2 * nocc)
    vir = slice(2 * nocc,nbas)

    kappa.reshape((nocc, nvirt))
    # Einsum pieces of Eqn 14 in response handout
    one = np.einsum('ab,jb->ja', F[occ, occ], kappa)
    two = np.einsum('ij,jb->ib', F[vir, vir], kappa)
    thr = np.einsum('jb,iajb->ia', kappa, g[occ, vir, occ, vir]) 
    fou = np.einsum('jb,ijab->ia', kappa, g[occ, vir, occ, vir])
    fiv = np.einsum('jb,bjai->ia', kappa, g[occ, vir, occ, vir])
    
    Fiakappa = - one + two + 4 * thr - fou - fiv

    Fiakappa.ravel()

    return Fiakappa




