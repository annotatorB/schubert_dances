# Milestone 2: [schubert_project.ipynb](https://nbviewer.jupyter.org/github/DCMLab/schubert_dances/blob/master/schubert_project.ipynb?flush_cache=true)
Use this link to view the notebook with interactive plots or clone the repo to run it.


# Prerequisites to run the notebook
This is a tested setup using a new conda environment but of course you can install everything in your root/base environment.

## Update your managers

    conda update conda
    conda update conda-build
    python -m pip install --upgrade pip
    
### And make sure to have ipykernel installed in all environments of which you might want to use the kernel
    
## (Either) Create new environment with required packages
Here with the arbitrary name `schubert`.

    conda create -n schubert python=3.7 nb_conda_kernels jupyter
    conda activate schubert
    conda install -c plotly plotly-orca psutil requests
    python -m pip install cufflinks Beautifulsoup4 lxml scipy
    
## (Or) Install them in an existing environment
    conda install nb_conda_kernels jupyter
    conda install -c plotly plotly-orca psutil requests
    python -m pip install --upgrade cufflinks Beautifulsoup4 lxml scipy
    
## (Optional) If you need Jupyter Lab

So far the notebook should run in Jupyter Notebook, but if, in addition, you want to use **Jupyter Lab**, you will need to follow these instructions taken from https://plot.ly/python/getting-started/#jupyterlab-support-python-35:

Install via `pip`:

    python -m pip install jupyterlab==1.2 ipywidgets>=7.5
    
or `conda:`

    conda install -c conda-forge jupyterlab=1.2
    conda install "ipywidgets=7.5"
    
Set system variable to avoid "JavaScript heap out of memory" errors during extension installation:

    # (OS X/Linux)
    export NODE_OPTIONS=--max-old-space-size=4096
    # (Windows)
    set NODE_OPTIONS=--max-old-space-size=4096

Then, run the following commands:

    # only if nodejs is missing
    conda -c conda-forge nodejs
    
    jupyter labextension install @jupyter-widgets/jupyterlab-manager@1.1 --no-build
    jupyter labextension install jupyterlab-plotly@1.3.0 --no-build
    jupyter labextension install plotlywidget@1.3.0 --no-build
    jupyter lab build

Then you can unset the system variable again:

    # (OS X/Linux)
    unset NODE_OPTIONS
    # (Windows)
    set NODE_OPTIONS=

