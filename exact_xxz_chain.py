import numpy as np
import numpy.linalg as npla
from itertools import product
import sys

EXACT_DIR = "./"

Sz = lambda state : state[0] if state[0] == state[1] else 0.0
Sm = lambda state : np.sqrt(S * (S + 1) - state[1] * (state[1] - 1)) if state[1] > state[0] else 0.0
Sp = lambda state : np.sqrt(S * (S + 1) - state[1] * (state[1] + 1)) if state[1] < state[0] else 0.0

def H_term(bra, ket):
    field_term = 0.0
    term = 0.0
    
    if bra == ket:
        for i in range(N-1):
            j = (i + 1) % N
            term += DELTA * Sz((bra[i], ket[i])) * Sz((bra[j], ket[j]))
        field_term = - H * np.sum(bra)
    else:        
        for i in range(N-1):
            j = (i + 1) % N
            ket_c = list(ket)
            
            tmp1 = Sp((bra[i], ket[i])) * Sm((bra[j], ket[j]))
            tmp2 = Sm((bra[i], ket[i])) * Sp((bra[j], ket[j]))
            if tmp1 != 0.0:
                ket_c[i] += 1
                ket_c[j] += -1
                if tuple(ket_c) == bra:
                    term += 0.5 * tmp1
            elif tmp2 != 0.0:
                ket_c[i] += -1
                ket_c[j] += 1
                if tuple(ket_c) == bra:
                    term += 0.5 * tmp2

    return J * term + field_term

S = float(sys.argv[1])
SPIN = list()
for m in range(int(2 * S + 1)):
    SPIN.append(-S + m)
J = 1.0
DELTA = float(sys.argv[2])
H = float(sys.argv[3])
N = 6

ALL_STATES = list(product(SPIN, repeat=N))
N_STATES = len(ALL_STATES)
stag_operator = np.zeros(N)
for i in range(N):
    stag_operator[i] = np.power(-1.0, i)

print("Creating Hamiltonian matrix")

H_matrix = np.zeros((N_STATES, N_STATES))
for i, bra in enumerate(ALL_STATES):
    for j, ket in enumerate(ALL_STATES):
        H_matrix[i, j] = H_term(bra, ket)

Sz_matrix = np.zeros((N_STATES, N_STATES))
for i in range(N_STATES):
    Sz_matrix[i, i] = np.sum(ALL_STATES[i])

Szs_matrix = np.zeros((N_STATES, N_STATES))
for i in range(N_STATES):
    Szs_matrix[i, i] = np.sum(stag_operator * np.array(ALL_STATES[i]))
    
print("Hamiltonian matrix created")
print("Diagonalizing Hamiltonian matrix")

E_vals, U = npla.eigh(H_matrix)
U_inv = npla.inv(U)
M_vals = np.diag(U_inv @ Sz_matrix @ U)
M2_vals = np.diag(U_inv @  np.power(Sz_matrix, 2.0) @ U)
Ms_vals = np.diag(U_inv @ Szs_matrix @ U)
M2s_vals = np.diag(U_inv @ np.power(Szs_matrix, 2.0) @ U)

print("Ended diagonalization")

T = np.arange(0.05, 2.0, 0.01)
T_vals = len(T)
beta = 1.0 / T

Z = np.array([np.sum(np.exp(- beta[i] * E_vals)) for i in range(T_vals)])

E = np.array([np.sum(E_vals * np.exp(- beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
E2 = np.array([np.sum(E_vals**2 * np.exp(- beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
C = np.array([beta[i]**2 * (E2[i] - E[i]**2) for i in range(T_vals)])
m = np.array([np.sum(M_vals * np.exp(-beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
m2 = np.array([np.sum(M2_vals * np.exp(-beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
m_sus = np.array([beta[i] * (m2[i] - m[i]**2) for i in range(T_vals)])

ms = np.array([np.sum(Ms_vals * np.exp(-beta[i] * E_vals)) / Z[i] for i in range(T_vals)])
m2s = np.array([np.sum(M2s_vals * np.exp(-beta[i] * E_vals)) / Z[i] for i in range(T_vals)])

E /= N
C /= N
m /= N
m2 /= N*N
m_sus /= N

ms /= N
m2s /= N*N

print("Starting to compute spin conductivity")
# g(\omega_k) = \omega_m \int_{0}^{\beta} d\tau \cos(\omega_k \tau) <P_y P_x(\tau)>
k_max = 5
x = N//2 - 1
y = x

Px = np.zeros((N_STATES, N_STATES))
Py = np.zeros((N_STATES, N_STATES))
for i in range(N_STATES):
    Px[i, i] = np.sum(ALL_STATES[i][x:])
    Py[i, i] = np.sum(ALL_STATES[i][y:])

H_matrix_diag = U_inv @ H_matrix @ U
Px_vals = U_inv @ Px @ U
Py_vals = U_inv @ Py @ U
Px_vals_tau = lambda tau: np.exp(tau * H_matrix_diag) @ Px_vals @ np.exp(-tau * H_matrix_diag)

w_k = np.zeros((T_vals, k_max))
g_spin = np.zeros((T_vals, k_max))

for k in range(1, k_max + 1):
    for j in range(T_vals):
        w_k[j, k - 1] = 2.0 * np.pi * k / beta[j]

        z = np.sum(np.exp(- beta[j] * E_vals))
        tau = np.arange(0.0, beta[j], 0.01)
        integral = np.zeros(len(tau))

        for i in range(len(tau)):
            integral[i] = np.cos(w_k[j, k - 1] * tau[i]) * np.sum(np.diag(Py_vals @ Px_vals_tau(tau[i])) * np.exp(- beta[j] * E_vals)) / z
        integral = np.trapz(integral, tau)
        
        g_spin[j, k - 1] = w_k[j, k - 1] * integral
print("Spin conductivity computed")

with open(EXACT_DIR + f"exact_N{N}_S{S}_delta{DELTA}_h{H}.csv", "w") as file:
    file.write("beta,E,C,m,m2,ms,m2s,m_sus\n")
    for i in range(T_vals):
        file.write(f"{beta[i]},{E[i]},{C[i]},{m[i]},{m2[i]},{ms[i]},{m2s[i]},{m_sus[i]}\n")
    
    for i in range(T_vals):
        file.write("beta\n")
        file.write(f"{beta[i]}\n")
        file.write("w_k,g_spin\n")
        for k in range(k_max):
            file.write(f"{w_k[j, k]},{g_spin[j, k]}\n")
