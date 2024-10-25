function start_jupyter(){
    local port="$1"

    if [[ -z "$port" ]]; then
        printf >&2 '%s ' "Enter the port number: "
        read port
    fi

    local running_pid=$(lsof -i ":${port}" -t)

    if [[ "$running_pid" ]]; then
        echo "Port $port is used by pid $running_pid. Choose a different port."
        return 1
    fi

    # Check if jupyterlab is installed in the current Pixi environment
    if ! pixi list | grep -q "jupyterlab"; then
        echo "Jupyter lab is not installed in the current Pixi environment."
        echo "Please install it using: pixi add jupyterlab"
        return 1
    fi

    nohup pixi run jupyter lab \
      --port=${port} \
      --allow-root \
      --notebook-dir=~ \
      >> ~/.jupyter/lab.log \
      2>/dev/null &

    sleep 2

    local server_info=$(pixi run jupyter server list --jsonlist 2> /dev/null)
    local jupyter_pid=$(echo "$server_info" | jq -r ".[] | select(.port==$port) | .pid")
    local jupyter_url=$(echo "$server_info" | jq -r ".[] | select(.port==$port) | .url")

    if [ -n "$jupyter_pid" ]; then
        local version=$(pixi run jupyter --version | head -n 1)
        echo "Running Jupyter lab version: $version at port: $port, pid: $jupyter_pid, URL: $jupyter_url"
        xdg-open "$jupyter_url"
    else
        echo "Failed to start Jupyter lab, check ~/.jupyter/lab.log for more details."
    fi
}
