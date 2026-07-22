# Table 1

Largest scale parameter (n) uncomputed within 30 seconds, sorted by Aw-Dep.

| Circuit | Param (n) | Aw-Dep | RwUn Sequential | RwUn Reverse | RwUn Jointly | RwUn Lifetime | Reqomp |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Clean IntegerComparator | controls | 0 | 10 | 100 | 20 | 20 | **170** |
| Clean MCX | controls | 0 | 30 | 460 | 210 | **1000+** | 170 |
| MCRY(pi/2) | controls | 0 | **1000+** | **1000+** | **1000+** | **1000+** | 14 |
| Clean Incrementer | operand | 0 | 7 | 100 | 16 | **750** | 190 |
| Deutsch-Jozsa | controls | 0 | X | X | X | **1000+** | 170 |
| Grover's algorithm | controls | 0 | X | X | X | **15** | 11\* |
| Dirty MCX | controls | 1 | 70 | 70 | 100 | **1000+** | 40\* |
| Clean Adder | per operand | 1 | 6 | 70 | 9 | 5 | **160** |
| Dirty IntegerComparator | controls | 4 | 13 | 13 | 19 | 15 | **30\*** |
| HighestBitConstAdder | operand | 4 | 9 | 9 | 12 | 9 | **20\*** |
| RiseConditionalCleanMCS | controls | 5 | **11** | 9 | X | 9 | X |
| ConditionalCleanMCS | controls | 6 | **1000+** | **1000+** | **1000+** | **1000+** | X |
| RiseConditionalDirtyMCS | controls | 7 | **7** | **7** | **7** | **7** | X |
| ConditionalDirtyMCS | controls | 11 | **1000+** | **1000+** | **1000+** | **1000+** | X |
| Gidney's Incrementer | operand | 61 (cycle) | X | X | **40** | X | X |
| Dirty Adder | per operand | 601 | 6 | 5 | 5 | **9** | X |
| Dirty Incrementer | operand | 803 | 9 | 9 | 9 | **50** | X |

Notes:

- Bold values are the largest successful scale in each row.
- `1000+` means scaling stopped at n = 1000.
- `n*` means Reqomp hit the recursion-depth limit.
- `X` means that the method failed for the tested range.
- `(cycle)` marks an aw-cycle in the dependency graph.
