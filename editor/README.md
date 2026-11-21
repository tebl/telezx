# ZX Editor (and related tools)


# Installation

## OS-dependencies
Different operating systems provide core functionality in different ways, requiring different steps to get the required version of Python as well as tkinter up and running. At most however I'm only one person, using at most a couple of them at a time (as any sane person would) so I can't provide much in the way of instructions for the rest of them. What I know, I've tried to include here.

### Fedora 45
```
sudo dnf install tk-devel
```

## pyenv
ZX Editor requires that you're running an up to date version of Python *>3.14*, if one has not been provided for you by the underlying Linux distribution - consider using [pyenv](https://github.com/pyenv/pyenv) to get around that. It's installed and activated like this:
```
curl -fsSL https://pyenv.run | bash
~/.pyenv/bin/pyenv init --install

pyenv install 3.15
pyenv global 3.15
```

You will need to restart your terminal windows at this point to ensure that nothing is still pointing towards the version of python included in your distribution. When that is done, you can go ahead and install the dependencies for this projet using the following command:

```
pip3 install -r requirements.txt
```
