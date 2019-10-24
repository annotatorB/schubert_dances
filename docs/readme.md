Setup was done following https://gist.github.com/GLMeece/222624fc495caf6f3c010a8e26577d31

To update the docs you might need to have these packages installed:
* sphinx
* sphinxcontrib-napoleon
* sphinx-rtd-theme

If you have created a new module, navigate to docs/ and use the command

    sphinx-apidoc -fo source/ ../tools

This generates 1 RST-file per python file. These files lie in source/

If you have updated one of the existing modules, a simple

    make html

will do. This generates the new HTML pages.

To change the structure of the startpage, edit the docs/source/index.rst file. Generally, you won't be doing much more than including the names of the generated RST-files in the TOC structure and changing their order.

# Setting such a thing up (for the future)

    pip install -U sphinx sphinxcontrib-napoleon sphinx-rtd-theme

Create docs/ folder, go in and run `sphinx-quickstart`.

Go to `docs/source/conf.py` and uncomment the three lines
    import os
    import sys
    sys.path.insert(0, os.path.abspath('.'))

Change the path '.' to the level from where to access the code folders, probably '../..'

In the list of extensions, include at least the first three of

    'sphinx.ext.autodoc',
    'sphinxcontrib.napoleon'
    'sphinx.ext.viewcode',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',

Find the `html_theme` option and change it to `html_theme = 'sphinx_rtd_theme'`

Now try `sphinx-apidoc -fo source/ ../code_folder` and `make html`. Solve the issues and go on. You end up with an `index.html` in one of the folders created during the `sphinx-quickstart`.

Go to the Repo-Options, activate the GithubPage for the Repo and change the `Source` to the docs/ folder. It has to be pushed by then.

Since the page is looking for the index.html within the top level of the docs/ folder, create a redirect called index.html with this source code:

    <html>
    <head>
    <meta http-equiv="refresh" content="0; url=build/html/index.html" />
    </head>
    <body></body>
    </html>

You should be good to go now. If you want to have your types rendered as links to the corresponding references, be sure you've included `'sphinx.ext.intersphinx'` in the extensions. Then you can add to your config file

    intersphinx_mapping = {
            'python': ('https://docs.python.org/3', None),
            'pandas': (' http://pandas.pydata.org/pandas-docs/stable/', None)}

In order to link to other references, be sure to provide the link leading to an `objects.inv` file. To link to BeautifulSoup, this trick had to be used, still in 2019: https://github.com/svenevs/exhale/tree/master/docs/_intersphinx
