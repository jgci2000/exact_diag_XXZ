import numpy as np
import numpy.linalg as npla
from itertools import product
import matplotlib
import matplotlib.pyplot as plt
import os
import pandas as pd

plt.style.use('seaborn')
matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'
HX = 5
HY = 4

SAVEFOLDER = "figures/"
OUTPUT_DIR = "SSE_results/"

Sz = lambda state : state[0] if state[0] == state[1] else 0.0
Sm = lambda state : 1.0 if state[1] > state[0] else 0.0
Sp = lambda state : 1.0 if state[1] < state[0] else 0.0

def H_term(bra, ket):
    term = 0.0
    
    if bra == ket:
        for i in range(N):
            j = (i + 1) % N
            term += Sz((bra[i], ket[i])) * Sz((bra[j], ket[j]))
    else:        
        for i in range(N):
            j = (i + 1) % N
            ket_c = list(ket)
            
            if Sp((bra[i], ket[i])) * Sm((bra[j], ket[j])) == 1.0:
                ket_c[i] = 1/2
                ket_c[j] = -1/2
                if ket_c == list(bra):
                    term += 0.5
            elif Sm((bra[i], ket[i])) * Sp((bra[j], ket[j])) == 1.0:
                ket_c[i] = -1/2
                ket_c[j] = 1/2
                if ket_c == list(bra):
                    term += 0.5

    return term

SPIN = [1/2, -1/2]
COLOR = ["r", "b", "g", "y", "k"]

for c, N in enumerate([2]):
    ALL_STATES = list(product(SPIN, repeat=N))
    N_STATES = len(ALL_STATES)

    H = np.zeros((N_STATES, N_STATES))
    for i, bra in enumerate(ALL_STATES):
        for j, ket in enumerate(ALL_STATES):
            H[i, j] = H_term(bra, ket)
    
    Sz = np.zeros((N_STATES, N_STATES))
    for i in range(N_STATES):
        Sz[i, i] = np.sum(ALL_STATES[i])

    for i in range(N_STATES):
        print(f"{ALL_STATES[i]} with {Sz[i, i]}")

    E_vals, U = npla.eigh(H)
    M_vals = npla.inv(U) @ Sz @ U

    beta = np.array([0.5, 1.0, 2.0, 4.0, 8.0, 16.0])
    T_vals = len(beta)
    T = 1.0 / beta
    
    Z = np.array([np.sum(np.exp(- beta[i] * E_vals)) for i in range(T_vals)])
    E = np.array([np.sum(E_vals * np.exp(- beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
    E /= N

    T_vals_sim = 6
    beta_sim = np.array([0.5, 1.0, 2.0, 4.0, 8.0, 16.0])
    T_sim = 1.0 / beta_sim
    
    E_sim = np.zeros(T_vals_sim)
    E_std = np.zeros(T_vals_sim)
    C_sim = np.zeros(T_vals_sim)
    C_std = np.zeros(T_vals_sim)
    m_sim = np.zeros(T_vals_sim)
    m_std = np.zeros(T_vals_sim)
    m2_sim = np.zeros(T_vals_sim)
    m2_std = np.zeros(T_vals_sim)
    ms_sim = np.zeros(T_vals_sim)
    ms_std = np.zeros(T_vals_sim)
    m2s_sim = np.zeros(T_vals_sim)
    m2s_std = np.zeros(T_vals_sim)
    m_sus_sim = np.zeros(T_vals_sim)
    m_sus_std = np.zeros(T_vals_sim)

    with open(OUTPUT_DIR + f"output_N{N}.csv", "r") as f:
        header = f.readline()
        for j in range(T_vals_sim):
            _, _, _, _, E_sim[j], E_std[j], C_sim[j], C_std[j], m_sim[j], m_std[j], m2_sim[j], m2_std[j], _, _, ms_sim[j], ms_std[j], m2s_sim[j], m2s_std[j], _, _, m_sus_sim[j], m_sus_std[j], _, _, _, _ = [float(x) for x in f.readline().strip().split(",")]

    print(f"{N=}")
    print("beta |  E Exact  |  SSE +/- std  |  in?")
    for i in range(T_vals):
        print(f"{beta[i]}  |  {E[i]}  |  {E_sim[i]} +/- {E_std[i]}  |  {True if (E[i] < E_sim[i] + E_std[i] and E[i] > E_sim[i] - E_std[i]) else False}")
    print()

    T = np.arange(0.01, 2.0, 0.01)
    T_vals = len(T)
    beta = 1.0 / T
    
    Z = np.array([np.sum(np.exp(- beta[i] * E_vals)) for i in range(T_vals)])

    E = np.array([np.sum(E_vals * np.exp(- beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
    E2 = np.array([np.sum(E_vals**2 * np.exp(- beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
    C = np.array([beta[i]**2 * (E2[i] - E[i]**2) for i in range(T_vals)])
    m = np.array([np.sum(M_vals * np.exp(-beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
    m2 = np.array([np.sum(M_vals**2 * np.exp(-beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
    m_sus = np.array([beta[i] * (m2[i] - m[i]**2) for i in range(T_vals)])

    E /= N
    C /= N
    m /= N
    m2 /= N
    m_sus /= N

    plt.figure(1, figsize=(HX, HY))
    plt.plot(T, E, "-" + COLOR[c],label=f"{N=}")
    plt.errorbar(T_sim, E_sim, E_std, fmt="--" + COLOR[c])
    plt.xlabel(r"$T$")
    plt.ylabel(r"$\langle E \rangle$")
    plt.legend()

    plt.figure(2, figsize=(HX, HY))
    plt.plot(T, C, "-" + COLOR[c],label=f"{N=}")
    plt.errorbar(T_sim, C_sim, C_std, fmt="--" + COLOR[c])
    plt.xlabel(r"$T$")
    plt.ylabel(r"$C$")
    plt.legend()
    
    plt.figure(3, figsize=(HX, HY))
    plt.plot(T, m, "-" + COLOR[c],label=f"{N=}")
    plt.errorbar(T_sim, m_sim, m_std, fmt="--" + COLOR[c])
    plt.xlabel(r"$T$")
    plt.ylabel(r"$\langle m \rangle$")
    plt.legend()
    
    plt.figure(4, figsize=(HX, HY))
    plt.plot(T, m2, "-" + COLOR[c],label=f"{N=}")
    plt.errorbar(T_sim, m2_sim, m2_std, fmt="--" + COLOR[c])
    plt.xlabel(r"$T$")
    plt.ylabel(r"$\langle m^2 \rangle$")
    plt.legend()

    plt.figure(5, figsize=(HX, HY))
    plt.plot(T, m_sus, "-" + COLOR[c],label=f"{N=}")
    plt.errorbar(T_sim, m_sus_sim, m_sus_std, fmt="--" + COLOR[c])
    plt.xlabel(r"$T$")
    plt.ylabel(r"$\chi$")
    plt.legend()

plt.show()