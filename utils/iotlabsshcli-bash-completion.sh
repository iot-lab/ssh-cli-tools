# iotlab-* completion

_iotlab_resources_list() {
    # TODO: complete `iotlab-ssh flash-m3 -l <tab>`
    COMPREPLY=()
}

_iotlab_ssh() {
    local cur prev words cword
    _init_completion || return

    case $prev in
        -v|--version|-h|--help)
            return 0
            ;;
        -u|--user|-p|--password)
            return 0
            ;;
    esac

    # Look for the command name
    local subcword cmd
    for (( subcword=1; subcword < ${#words[@]}-1; subcword++ )); do
        [[ ${words[subcword]} != -* && \
            ! ${words[subcword-1]} =~ -+(jmespath|jp|format|fmt|u(ser)?|p(assword)) ]] && \
                { cmd=${words[subcword]}; break; }
    done

    if [[ -z $cmd ]]; then
        case $cur in
            -*)
                # No command name, complete with generic flags
                COMPREPLY=($(compgen -W '-h --help -u --user -p --password -v --version --jmespath --jp --format --fmt -i --id --verbose' -- "$cur" ))
                return 0
                ;;
            *)
                # Complete with a command name
                COMPREPLY=($(compgen -W 'flash-m3 reset-m3 wait-for-boot run-script run-cmd copy-file' -- "$cur"))
                return 0
                ;;
        esac
    fi

    # Complete command arguments
    case $cmd in
        flash-m3|copy-file)
            case "$prev" in
                -u|--user|-p|--password)
                    # Nothing to complete
                    ;;
                -e|--exclude)
                    _iotlab_resources_list
                    ;;
                -l|--list)
                    _iotlab_resources_list
                    ;;
                -*)
                    COMPREPLY=($(compgen -W '-h --help -u --user -p --password -v --version -e --exclude -l --list' -- "$cur" ))
                    ;;
                *)
                    _filedir
            esac
            ;;
        reset-m3)
            case "$prev" in
                -u|--user|-p|--password)
                    # Nothing to complete
                    ;;
                -e|--exclude)
                    _iotlab_resources_list
                    ;;
                -l|--list)
                    _iotlab_resources_list
                    ;;
                *)
                    COMPREPLY=($(compgen -W '-h --help -u --user -p --password -v --version -e --exclude -l --list' -- "$cur" ))
            esac
            ;;
        wait-for-boot)
            case "$prev" in
                -u|--user|-p|--password|--max-wait)
                    # Nothing to complete
                    ;;
                -e|--exclude)
                    _iotlab_resources_list
                    ;;
                -l|--list)
                    _iotlab_resources_list
                    ;;
                *)
                    COMPREPLY=($(compgen -W '-h --help -u --user -p --password -v --version --max-wait -e --exclude -l --list' -- "$cur" ))
            esac
            ;;
        run-script|run-cmd)
            case "$prev" in
                -u|--user|-p|--password)
                    # Nothing to complete
                    ;;
                -e|--exclude)
                    _iotlab_resources_list
                    ;;
                -l|--list)
                    _iotlab_resources_list
                    ;;
                -*)
                    COMPREPLY=($(compgen -W '-h --help -u --user -p --password -v --version --frontend -e --exclude -l --list' -- "$cur" ))
                    ;;
                *)
                    _filedir
            esac
    esac
}

complete -F _iotlab_ssh iotlab-ssh
