Setup was done following https://gist.github.com/GLMeece/222624fc495caf6f3c010a8e26577d31

To update the docs you might need to have these packages installed:
* sphinx
* sphinxcontrib-napoleon
* sphinx-rtd-theme

If you have created a new module, navigate to docs/ and use the command

    sphinx-apidoc -fo source/ ../tools

This generates 1 RST-file per python file. These files lie in source/

If you have update one of the existing modules, a simple

    make html

will do. This generates the new HTML pages.

To change the structure of the startpage, edit the docs/source/index.rst file. Generally, you won't be doing much more than including the names of the generated RST-files in the TOC structure and changing their order.