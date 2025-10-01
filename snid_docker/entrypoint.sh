#!/bin/bash
set -e

echo "ENTRYPOINT START: user=$(whoami), args=$*"

# Directories that need write access
dirs_to_fix=(
    /snid_api_runs
    /media/snid_template_options
)

for dir in "${dirs_to_fix[@]}"; do
    if [ -d "$dir" ]; then
        # Check if directory is writable by current user
        if [ -w "$dir" ]; then
            echo "$dir is writable, skipping chown"
        else
            echo "Attempting chown on $dir"
            # Only attempt chown if it fails, ignore errors (bind mounts may fail)
            chown -R sniduser:snidgroup "$dir" || echo "Warning: cannot chown $dir, skipping"
        fi
    else
        echo "Directory $dir does not exist, creating"
        mkdir -p "$dir"
        chown sniduser:snidgroup "$dir" || echo "Warning: cannot chown $dir, skipping"
    fi
done

# Execute the main container command as sniduser
exec su -s /bin/bash sniduser -c "$@"
