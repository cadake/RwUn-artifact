# Table 1

Largest tested scale parameter (n <= 1000) uncomputed within 30 seconds using a fixed-step search, sorted by Aw-Dep.

| Circuit | Param (n) | Aw-Dep | RwUn Sequential | RwUn Reverse | RwUn Jointly | RwUn Lifetime | Reqomp |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Clean IntegerComparator | controls | 0 | 10 | 160 | 20 | 20 | **210** |
| Clean MCX | controls | 0 | 40 | 650 | 260 | **1000+** | 210 |
| MCRY(pi/2) | controls | 0 | **1000+** | **1000+** | **1000+** | **1000+** | 15 |
| Clean Incrementer | operand | 0 | 10 | 190 | 103 | **450** | 210 |
| Deutsch-Jozsa | controls | 0 | X | X | X | **1000+** | 210 |
| Grover's algorithm | controls | 0 | X | X | X | **16** | 14 |
| Piecewise Linear Rotation | state qubits | 0 | X | X | X | X | **10** |
| Polynomial Pauli Rotation | state qubits | 0 | X | X | X | X | **10** |
| Weighted Adder | state qubits | 0 | 3 | 3 | 3 | 93 | **269** |
| Dirty MCX | controls | 1 | 90 | 90 | 130 | **1000+** | **1000+** |
| Clean Adder | per operand | 1 | 6 | 130 | 10 | 6 | **210** |
| Dirty IntegerComparator | controls | 4 | 15 | 13 | 21 | 17 | **1000+** |
| HighestBitConstAdder | operand | 4 | 9 | 9 | 13 | 10 | **1000+** |
| RiseConditionalCleanMCS | controls | 5 | **12** | 9 | 9 | 9 | X |
| ConditionalCleanMCS | controls | 6 | **1000+** | **1000+** | **1000+** | **1000+** | X |
| RiseConditionalDirtyMCS | controls | 7 | 7 | 7 | 7 | **9** | X |
| ConditionalDirtyMCS | controls | 11 | **1000+** | **1000+** | **1000+** | **1000+** | X |
| Multiplier | per operand | 27 | 3 | 3 | 3 | 6 | **42** |
| Gidney's Incrementer | operand | 61 (cycle) | X | X | **49** | X | X |
| Dirty Adder | per operand | 601 | 6 | 6 | 5 | **10** | X |
| Dirty Incrementer | operand | 803 | 10 | 10 | 10 | **100** | X |

Notes:

- Bold values are the largest successful scale in each row.
- `1000+` means scaling stopped at n = 1000.
- `n*` marks a recursion-depth failure during the search.
- `X` means no successful tested scale was recorded, or the method was not tested; it does not distinguish timeout from algorithm failure. See the run log for each attempt.
- `(cycle)` marks an aw-cycle in the dependency graph.
