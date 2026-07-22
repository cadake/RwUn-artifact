# RwUn Artifact

This artifact contains the RwUn implementation, circuit examples, the vendored Reqomp baseline, the scripts used to reproduce the evaluation results reported in the paper, and the reference results reported in the paper.

## Artifact Organization

| Path | Description |
| --- | --- |
| `RwUn/` | RwUn implementation and circuit examples |
| `Reqomp-master/` | Vendored Reqomp baseline |
| `run_evaluation.py` | Entry point for smoke tests and evaluation |
| `dist/` | Prebuilt Docker image and checksum files |
| `paper_data/` | Reference table and plots reported in the paper |

The evaluation script supports the following modes:

| Mode | Purpose | Approximate runtime | Main outputs |
| --- | --- | ---: | --- |
| `0` | Smoke tests | Less than 1 minute | Test results printed to the terminal |
| `1` | Evaluation, part 1 | 1 hour | `evaluation/table1_merged.md` |
| `2` | Evaluation, quick part 2 | 4 hours | `evaluation/quick/qfree_metrics.pdf, evaluation/quick/success_quan.pdf` |
| `3` | Evaluation, full part 2 | 18 hours | `evaluation/full/qfree_metrics.pdf, evaluation/full/success_quan.pdf` |

All runtimes reported above were measured on:

- CPU: i9-14900HX
- Memory: 64GB
- Operating system: Linux under WSL2
- Docker version: 28.5.2

Actual runtimes may vary across machines.

## Kick the Tires

### Install

Docker is the recommended way to evaluate the artifact. The supplied
image was validated on Linux amd64 with Docker 28.5.2. ARM-based
containers have not been validated.


##### Option A: Load the Prebuilt Image

The artifact includes a prebuilt Linux amd64 image. To load it, run:

```bash
gzip --decompress --stdout dist/rwun-artifact-image-linux-amd64.tar.gz \
  | docker load
```

##### Option B: Build the Image

From the artifact root directory, run:

```bash
docker build --tag rwun-artifact:2026 .
```

### Smoke Test

Run:

```bash
docker run --rm --network none \
  --user "$(id -u):$(id -g)" \
  rwun-artifact:2026 \
  python run_evaluation.py 0
```
Expect `Ran 2 tests ... OK` in under one minute.


## Evaluation

Create a directory in which the generated results will be stored:
```bash
mkdir -p evaluation
```
To recompute the practical benchmark results reported in [refer-table1](paper_data/table1.png) (Table 1, Section 7.2), run:
```bash
docker run --rm --network none \
  --user "$(id -u):$(id -g)" \
  --volume "$PWD/evaluation:/artifact/evaluation" \
  rwun-artifact:2026 \
  python run_evaluation.py 1
```

This takes approximately one hour and the main generated file is:
```
evaluation/table1_merged.md
```

##### Quick Random Evaluation

To recompute the randomized qfree and quantum results reported in [refer-qfree](paper_data/qfree.png) (Fig. 10, Section 7.2) and [refer-quan](paper_data/quan.png) (Fig. 11, Section 7.2), we recommond running quick evaluation with mode `2`:

```bash
docker run --rm --network none \
  --user "$(id -u):$(id -g)" \
  --volume "$PWD/evaluation:/artifact/evaluation" \
  rwun-artifact:2026 \
  python run_evaluation.py 2
```

The main generated files are:
```
evaluation/quick/qfree_metrics.pdf
evaluation/quick/success_quan.pdf
```

Mode `2` uses the same generators, algorithms, and random seed as the paper evaluation. It just does not run last several points of big scale.

##### Optional Full Random Evaluation


Full random evaluation may take approximately 18 hours. Run with mode `3`:
```
docker run --rm --network none \
  --user "$(id -u):$(id -g)" \
  --volume "$PWD/evaluation:/artifact/evaluation" \
  rwun-artifact:2026 \
  python run_evaluation.py 3
```

And the main result files will be:
`evaluation/full/qfree_metrics.pdf`, `evaluation/full/success_quan.pdf`


## Paper Claims and Supporting Evidence

| Evalutaion target (Applicability and Scalability)                             | Paper reference |  mode | Generated evidence                  | Reviewer check                          |
| --------------------------------------- | -------------- | --------------: | ----------------------------------- | --------------------------------------- |
| Practical benchmark          | [refer-table1](paper_data/table1.png)(Table 1, Section 7.2)        |             `1` |`evaluation/table1_merged.md`  | The positions marked with `X`, indicating failures, should match exactly between the two tables. Each numerical entry is the largest scale that can be completed within 30 seconds. The numerical values should be broadly similar, but some differences are expected because runtime depends on the machine.                              |
|  Random qfree circuits | [refer-qfree](paper_data/qfree.png)(Fig. 10, Section 7.2)    |      `2/3` | `qfree_metrics.pdf` | Reproduces the referrenced figure, except that mode `2` omits the final few data points.        |
| Random quantum circuits                 | [refer-quan](paper_data/quan.png)(Fig. 11, Section 7.2)    |      `2/3` | `success_quan.pdf`  | Reproduces the referrenced figure, except that mode `2` omits the final few data points.  |

Evaluaion modes 2 and 3 use random seed 42, matching the paper evaluation. This fixes the generated benchmark instances.




## Native Installation

Docker is recommended for artifact evaluation. The following native
installation is provided for users who want to use RwUn directly.

### Install RwUn


Create and activate a Conda environment:
```bash
conda create --name rwun --yes python=3.10.18 pip=25.1
conda activate rwun
```

Install the pinned dependencies and RwUn:
```
python -m pip install --requirement requirements-lock.txt
python -m pip install --no-deps .
```


### Usage Example

```python
from RwUn.uncomp import uncompute
from qiskit.circuit import QuantumRegister, QuantumCircuit, AncillaRegister

if __name__ == "__main__":
    q = QuantumRegister(3)
    t = QuantumRegister(1)
    a = AncillaRegister(1)
    C = QuantumCircuit(q,t,a)
    C.ccx(q[0],q[1],a[0])
    C.ccx(a[0],q[2],t[0])

    print(C)
    # q0_0: ──■───────
    #         │       
    # q0_1: ──■───────
    #         │       
    # q0_2: ──┼────■──
    #         │  ┌─┴─┐
    #   q1: ──┼──┤ X ├
    #       ┌─┴─┐└─┬─┘
    #   a0: ┤ X ├──■──
    #       └───┘     

    # uncompute ancilla a as clean ancilla
    D = uncompute(C, 0)
    print(D)
    # q0_0: ──■─────────■──
    #         │         │  
    # q0_1: ──■─────────■──
    #         │         │  
    # q0_2: ──┼────■────┼──
    #         │  ┌─┴─┐  │  
    #   q1: ──┼──┤ X ├──┼──
    #       ┌─┴─┐└─┬─┘┌─┴─┐
    #   a0: ┤ X ├──■──┤ X ├
    #       └───┘     └───┘

    # uncompute a as dirty ancilla
    E = uncompute(C, 3)
    print(E)
    # q0_0: ──■──
    #         │  
    # q0_1: ──■──
    #         │  
    # q0_2: ──■──
    #       ┌─┴─┐
    #   q1: ┤ X ├
    #       └───┘
    #   a0: ─────
```

### Native Evaluation with Reqomp

To reproduce the paper evaluation without Docker, install the vendored
Reqomp baseline:

```bash
python -m pip install --no-deps ./Reqomp-master
```
Then run:
```
python run_evaluation.py 1
python run_evaluation.py 3
```







