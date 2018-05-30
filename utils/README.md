# Miscellaneous utilities for iotlab-cli-tools

## Bash-completion

The script `iotlabsshcli-bash-completion.sh` is available to complete the
`iotlab-ssh` command.  It is compatible with the standard bash-completion
mechanism, as many commands are in https://github.com/scop/bash-completion.
The scripts only needs to be sourced at runtime from command-line:

    source iotlabsshcli-bash-completion.sh

Then, bash is able to autocomplete the iotlab-ssh commands:

    iotlab-ssh <press tab key here>


One also wants to install it on a whole system, to be automatically available
for all users:

    sudo install -m644 iotlabsshcli-bash-completion.sh /usr/share/bash-completion/completions/iotlab-ssh

Cf. https://github.com/scop/bash-completion for more details.
