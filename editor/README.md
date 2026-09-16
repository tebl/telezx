# ZX Editor (and related tools)


## Dependencies
ZX Editor requires that you're running an up to date version of Python *>3.14*, if one has not been provided for you by the underlying Linux distribution - consider using [pyenv](https://github.com/pyenv/pyenv) to get around that. It's installed and activated like this:
```
curl -fsSL https://pyenv.run | bash
~/.pyenv/bin/pyenv init --install

pyenv install 3.14
pyenv global 3.14
```

You will need to restart your terminal windows at this point to ensure that nothing is still pointing towards the version of python included in your distribution. When that is done, you can go ahead and install the dependencies for this projet using the following command:

```
pip3 install -r requirements.txt
```
