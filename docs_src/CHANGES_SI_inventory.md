

Derived from the code (every IBM result goes through `src.ibm.run_ibm`, directly or via
`src.runners.ibm_replicate`; the Markov chain lives in `src/rare_exploration.py`).

| Result file | Section | Depends on IBM / Markov chain | Mean-field only parts |
|---|---|---|---|
| rep_b1b2 | B1, B2 | no | all |
| rep_fig3 | Fig. 3 orbits, D3, D6 | no | all |
| rep_shrinkage | orbit shrinkage, Hopf in mu | no | all |
| rep_markov | B3 Markov ratio, derived T | Markov chain (T derivation) | n/a |
| rep_b3 | B3 simulated ratio, scan, SE check | IBM (small) | none |
| rep_b4_small | B4 cycles (Fig. 1) | IBM (small) | none |
| rep_b4_large | B4 damped oscillations (Fig. 2A) | IBM (large) | exact mean field of the IBM, eigenvalues |
| rep_validation | IBM vs exact mean field (Fig. 10A) | IBM (large rates) | reference ODE |
| ext_bif | SNIC, rho_c, two-parameter diagram | no | all |
| ext_e1 | rho x h | IBM part (ibm_small) | meanfield, critical |
| ext_e2 | rho x kappa (V1-V3), V1 equivalence | IBM part (ibm_small) | meanfield_V1..V3 |
| ext_e3 | time series | IBM part (ibm_small series) | meanfield series |
| ext_e4 | H1, H2 finite population | IBM (small and large) | none |
| ext_e5 | V2 hysteresis, scan | IBM part (ibm_small two starts) | hysteresis, fold curve, scan |
| ext_e5b | V2 follow-up | IBM part (ibm two starts) | maps, sweeps |
| ext_e6 | V3 delay stability | no | all |
| sens_oat | sensitivity | IBM part (ibm_large_s, s identity check) | meanfield OAT |
| sens_pulse | pulses vs continuous | IBM part (ibm_small) | meanfield |
| sens_altA | A = 0.7 | IBM part (ibm_small) | meanfield, critical |
| sens_p0 | p0 < 1 | IBM part (ibm_small) | meanfield, critical |
| sens_finite | finite size | IBM | none |
| sens_explo | other exploration rates | no | all |
| sens_numerics | tolerance and grid checks | no | all |
| sens_se | SE vs replicates | IBM | none |

Figures with IBM or Markov content: Fig. 1 (fig01), Fig. 2 panel A (fig02), Fig. 3 (fig03),
Fig. 5 panel C (fig05), Fig. 6 panels D-F (fig07 file), Fig. 7 panels D-F (fig06 file),
Fig. 8 panel E (fig08), Fig. 10 (fig10), Fig. S1 bottom row, Fig. S4 (new). Mean-field only: Fig. 4 (fig04),
Fig. 9 (fig09), Fig. S2, Fig. S3, and the mean-field panels of the figures above.
