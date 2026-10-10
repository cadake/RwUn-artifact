# Table 1

Largest tested scale parameter (n <= 1000) uncomputed within 30 seconds using a fixed-step search, sorted by Aw-Dep.

| Circuit | Param (n) | Aw-Dep | RwUn Sequential | RwUn Reverse | RwUn Jointly | RwUn Lifetime | Reqomp |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Clean IntegerComparator | controls | 0 | 10 | 130 | 20 | 20 | **180** |
| Clean MCX | controls | 0 | 30 | 480 | 240 | **1000+** | 190 |
| MCRY(pi/2) | controls | 0 | **1000+** | **1000+** | **1000+** | **1000+** | 14 |
| Clean Incrementer | operand | 0 | 9 | 140 | 89 | **350** | 170 |
| Deutsch-Jozsa | controls | 0 | X | X | X | **1000+** | 170 |
| Grover's algorithm | controls | 0 | X | X | X | **15** | 13 |
| Piecewise Linear Rotation | state qubits | 0 | X | X | X | X | **9** |
| Polynomial Pauli Rotation | state qubits | 0 | X | X | X | X | **10** |
| Weighted Adder | state qubits | 0 | 3 | 3 | 3 | 84 | **219** |
| Dirty MCX | controls | 1 | 70 | 70 | 100 | **1000+** | **1000+** |
| Clean Adder | per operand | 1 | 6 | 80 | 9 | 5 | **160** |
| Dirty IntegerComparator | controls | 4 | 13 | 13 | 19 | 15 | **850** |
| HighestBitConstAdder | operand | 4 | 9 | 8 | 12 | 9 | **970** |
| RiseConditionalCleanMCS | controls | 5 | **11** | 9 | 7 | 9 | X |
| ConditionalCleanMCS | controls | 6 | **1000+** | **1000+** | **1000+** | **1000+** | X |
| RiseConditionalDirtyMCS | controls | 7 | 7 | 7 | 7 | **9** | X |
| ConditionalDirtyMCS | controls | 11 | **1000+** | **1000+** | **1000+** | **1000+** | X |
| Multiplier | per operand | 27 | 3 | 3 | 3 | 6 | **38** |
| Gidney's Incrementer | operand | 61 (cycle) | X | X | **45** | X | X |
| Dirty Adder | per operand | 601 | 6 | 6 | 5 | **9** | X |
| Dirty Incrementer | operand | 803 | 10 | 10 | 10 | **90** | X |

Notes:

- Bold values are the largest successful scale in each row.
- `1000+` means scaling stopped at n = 1000.
- `n*` marks a recursion-depth failure during the search.
- `X` means no successful tested scale was recorded, or the method was not tested; it does not distinguish timeout from algorithm failure. See the run log for each attempt.
- `(cycle)` marks an aw-cycle in the dependency graph.
