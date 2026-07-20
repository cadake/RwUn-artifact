## Reproduce Evaluation

### Organization

The RwUn implementation is made up of the files in the folder [RwUn](/RwUn/).

All examples presented in the submitted paper can be found in [RwUn/examples](RwUn/examples).


### Install
```
conda create --name rwun --yes python=3.10
conda activate rwun

cd Reqomp-master
pip install .

cd ../RwUn
pip install .
```

### Run

For quick run:
```
python run_evaluation.py 1
```

For full run:
```
python run_evaluation.py 2
```

Results will be in the [evaluation](evaluation) folder, with `dependency_result` correponds to **Aw-Dep** column in Table 1 and **Aw-Dep: S/D** column in Table 3. `table1_result` corresponds to other columns in Table 1 and Table 3. [evaluation_results](evaluation_results) already contains the full results.
