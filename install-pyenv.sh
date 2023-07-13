# install pyenv
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/shims:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# install pyenv-virtualenv
git clone https://github.com/yyuu/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
exec $SHELL -l
source ~/.bashrc


cat <<EOF > ~/.pyenv/bin/pyenvs
#!/bin/bash
export PATH="\$HOME/.pyenv/bin:\$PATH"
eval "\$(pyenv init -)"
eval "\$(pyenv virtualenv-init -)"
#. /home/\$USER/.bashrc

if [ \$# -lt 2 ]; then
    echo "Usage: pyenvs <python_version> <script_path> <script_arguments>"
    exit 1
fi

python_version="\$1"
script_path="\$2"
shift 2  # Shift the arguments to exclude the Python version and script path
script_args="\$@"

# Check if the specified Python version exists
if ! pyenv versions | grep -q " \$python_version"; then
    echo "Error: Python version '\$python_version' does not exist."
    echo "Available versions:"
    pyenv versions
    exit 1
fi

pyenv shell "\$python_version"
cd "\$(dirname "\$script_path")"

if [ \${#script_args} -lt 1 ]; then
    python "\$(basename "\$script_path")"
else
    python "\$(basename "\$script_path")" "\$script_args"
fi

# usage in crontab 
# 0 8 * * * pyenvs <python_version> <script_path> <script_arguments>
EOF

chmod +x ~/.pyenv/bin/pyenvs
