#!/bin/bash
# AutoTaggingOpenSource Project Setup Script for Debian-based Systems (Optimized for Ubuntu for Docker setup)
# This script automates the initial setup of the Python virtual environment
# and installation of project dependencies.
# IT WILL ATTEMPT TO INSTALL MISSING SYSTEM PREREQUISITES, INCLUDING DOCKER,
# AND ADD THE INVOKING USER TO THE DOCKER GROUP.
# --- !! WARNING !! ---
# This script is configured to require root privileges (sudo) AND
# will attempt to install system software like Docker, Python, Git, etc.,
# and modify user group memberships.
# Running this script as root and allowing it to install packages carries
# inherent risks. Ensure you understand the commands being executed.
# PROCEED WITH EXTREME CAUTION.
# ---------------------
# Exit immediately if a command exits with a non-zero status.

set -e

# --- Sudo Check ---
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script is configured to be run as root to install system packages." >&2
    echo "Please re-run using 'sudo $0'" >&2
    exit 1
fi
echo "--- Running with root privileges (UID: $(id -u)) ---"
if [ -n "$SUDO_USER" ]; then
    echo "Original user (invoked sudo): $SUDO_USER (UID: $SUDO_UID, GID: $SUDO_GID)"
else
    echo "Warning: SUDO_USER not detected. Some user-specific post-setup steps (like docker group addition or file ownership) might require manual intervention for your specific user."
fi
echo "WARNING: This script will attempt to install system packages like git, Python, Docker, etc."
echo "This script is for Debian-based systems; Docker installation steps are optimized assuming an Ubuntu environment."
echo "----------------------------------------------------------------------------------"
echo ""
# --- End Sudo Check ---

# --- Configuration ---
VENV_DIR=".venv"
MIN_PYTHON_VERSION_MAJOR=3
MIN_PYTHON_VERSION_MINOR=12
PYTHON_VERSION_STRING="${MIN_PYTHON_VERSION_MAJOR}.${MIN_PYTHON_VERSION_MINOR}"
TARGET_PYTHON_CMD="python${PYTHON_VERSION_STRING}"
PYTHON_CMD_TO_USE=""
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# --- Package Management (Debian/Apt specific) ---
PKG_UPDATE_CMD="apt-get update -qq"
PKG_INSTALL_CMD="apt-get install -y -qq"
APT_UPDATED_THIS_RUN=""

install_apt_packages() {
    if [ -z "$APT_UPDATED_THIS_RUN" ]; then
        echo "Running package list update ($PKG_UPDATE_CMD)..."
        if ! $PKG_UPDATE_CMD; then
            echo "Error: 'apt-get update' failed. Please check your network connection and APT sources."
            exit 1
        fi
        APT_UPDATED_THIS_RUN=true
    fi
    echo "Attempting to install via apt: $*"
    # shellcheck disable=SC2086
    if ! $PKG_INSTALL_CMD "$@"; then
        echo "Error: Failed to install one or more apt packages: $*."
        echo "This script attempted to install them automatically but failed."
        echo "Please check for errors above (e.g., network issues, broken packages, repository problems)."
        echo "You may need to resolve these system-level APT issues manually and then re-run the script."
        exit 1
    fi
    echo "Successfully installed/verified via apt: $*"
}

ensure_git_installed() {
    echo "--- Ensuring Git is installed ---"
    if command -v git &> /dev/null; then
        echo "Git is already installed: $(git --version)"
        return
    fi
    echo "Git not found. Attempting to install via apt..."
    install_apt_packages git
    if ! command -v git &> /dev/null; then
        echo "Error: Git installation failed even after an attempt. Please check APT logs."
        exit 1
    fi
    echo "Git installed successfully."
    echo "-------------------------------"
}

ensure_python_installed() {
    echo "--- Ensuring Python $PYTHON_VERSION_STRING is installed ---"
    if command -v "$TARGET_PYTHON_CMD" &> /dev/null; then
        local ver_major=$($TARGET_PYTHON_CMD -c "import sys; print(sys.version_info.major)")
        local ver_minor=$($TARGET_PYTHON_CMD -c "import sys; print(sys.version_info.minor)")
        if [[ "$ver_major" -eq "$MIN_PYTHON_VERSION_MAJOR" && "$ver_minor" -eq "$MIN_PYTHON_VERSION_MINOR" ]]; then
            PYTHON_CMD_TO_USE="$TARGET_PYTHON_CMD"
            echo "Found suitable Python: $PYTHON_CMD_TO_USE ($($PYTHON_CMD_TO_USE -V))"
            return
        else
            echo "Found $TARGET_PYTHON_CMD but it's version $ver_major.$ver_minor, not ${PYTHON_VERSION_STRING}. Will attempt reinstall/update."
        fi
    fi
    echo "Python $PYTHON_VERSION_STRING ($TARGET_PYTHON_CMD) not found or incorrect version. Attempting to install..."
    echo "This will use the 'deadsnakes' PPA for Python."
    echo "Ensuring 'software-properties-common' (for add-apt-repository) is installed..."
    install_apt_packages software-properties-common
    if ! command -v add-apt-repository &> /dev/null; then
        echo "Error: add-apt-repository command not found even after attempting to install software-properties-common."
        echo "Cannot add PPA. Please ensure 'software-properties-common' can be installed correctly on your system."
        exit 1
    fi
    echo "Adding deadsnakes PPA..."
    if ! add-apt-repository -y ppa:deadsnakes/ppa; then
        echo "Error: Failed to add deadsnakes PPA. Please check for errors above."
        exit 1
    fi
    APT_UPDATED_THIS_RUN=""
    echo "Installing python${PYTHON_VERSION_STRING}, python${PYTHON_VERSION_STRING}-venv, python${PYTHON_VERSION_STRING}-dev..."
    install_apt_packages "python${PYTHON_VERSION_STRING}" "python${PYTHON_VERSION_STRING}-venv" "python${PYTHON_VERSION_STRING}-dev"
    if ! command -v "$TARGET_PYTHON_CMD" &> /dev/null; then
        echo "Error: $TARGET_PYTHON_CMD still not found after attempting installation from PPA."
        exit 1
    fi
    PYTHON_CMD_TO_USE="$TARGET_PYTHON_CMD"
    echo "$PYTHON_CMD_TO_USE installed/found: $($PYTHON_CMD_TO_USE -V)"
    echo "----------------------------------------------------"
}

check_python_final_version_and_venv() {
    echo "--- Verifying final Python version and venv module ---"
    if [ -z "$PYTHON_CMD_TO_USE" ]; then
        echo "Error: PYTHON_CMD_TO_USE is not set. Python installation or detection failed."
        exit 1
    fi
    if ! command -v "$PYTHON_CMD_TO_USE" &> /dev/null; then
        echo "Error: Command '$PYTHON_CMD_TO_USE' not found after all attempts. Cannot proceed."
        exit 1
    fi
    local PY_VERSION_FULL
    PY_VERSION_FULL=$($PYTHON_CMD_TO_USE -V 2>&1)
    local PY_ACTUAL_MAJOR PY_ACTUAL_MINOR
    if [[ $PY_VERSION_FULL =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
        PY_ACTUAL_MAJOR=${BASH_REMATCH[1]}
        PY_ACTUAL_MINOR=${BASH_REMATCH[2]}
    else
        echo "Error: Could not parse Python version from '$PY_VERSION_FULL' using $PYTHON_CMD_TO_USE."
        exit 1
    fi
    echo "Final Python version check: $PY_ACTUAL_MAJOR.$PY_ACTUAL_MINOR (using $PYTHON_CMD_TO_USE)"
    if [ "$PY_ACTUAL_MAJOR" -ne "$MIN_PYTHON_VERSION_MAJOR" ] || \
       [ "$PY_ACTUAL_MINOR" -ne "$MIN_PYTHON_VERSION_MINOR" ]; then
        echo "Error: Final Python version $PY_ACTUAL_MAJOR.$PY_ACTUAL_MINOR does not match required $PYTHON_VERSION_STRING."
        exit 1
    fi
    echo -n "Checking for Python's 'venv' module with $PYTHON_CMD_TO_USE... "
    if ! $PYTHON_CMD_TO_USE -m venv -h &> /dev/null; then
        echo "NOT FOUND."
        echo "Error: Python's 'venv' module is not available with $PYTHON_CMD_TO_USE."
        echo "Attempting to reinstall python${PYTHON_VERSION_STRING}-venv..."
        install_apt_packages "python${PYTHON_VERSION_STRING}-venv"
        if ! $PYTHON_CMD_TO_USE -m venv -h &> /dev/null; then
            echo "Error: Failed to make 'venv' module available after re-attempt. Please check APT logs."
            exit 1
        fi
    fi
    echo "Found."
    echo "----------------------------------------------------"
}

ensure_build_tools_installed() {
    echo "--- Ensuring Build Tools (build-essential) are installed ---"
    install_apt_packages build-essential
    echo "Build tools (build-essential) checked/installed."
    echo "----------------------------------------------------"
}

ensure_docker_installed() {
    echo "--- Ensuring Docker Engine and Compose V2 plugin are installed (assuming Ubuntu) ---"
    if command -v docker &> /dev/null && docker --version &> /dev/null; then
        echo "Docker Engine is already installed: $(docker --version)"
        if docker compose version &> /dev/null; then
            echo "Docker Compose V2 plugin is also available: $(docker compose version)"
            # Skip to user group check if Docker is already fully installed
        else
            echo "Docker Engine is installed, but Docker Compose V2 plugin seems missing."
            echo "Will attempt to install/update Docker components."
        fi
    else
        echo "Docker Engine not found or not working. Attempting to install..."
    fi

    if ! (command -v docker &> /dev/null && docker compose version &> /dev/null); then
        echo "Preparing for Docker installation (installing prerequisites)..."
        install_apt_packages ca-certificates curl gnupg lsb-release
        echo "Adding Docker's official GPG key..."
        sudo install -m 0755 -d /etc/apt/keyrings
        if curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg; then
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo "Docker GPG key added successfully."
        else
            echo "Error: Failed to download and add Docker's GPG key for Ubuntu."
            exit 1
        fi
        echo "Setting up Docker's apt repository for Ubuntu..."
        local ubuntu_codename
        if command -v lsb_release &> /dev/null; then
            ubuntu_codename=$(lsb_release -cs)
        elif [ -f /etc/os-release ]; then
            echo "Warning: 'lsb_release' command not found. Falling back to /etc/os-release for Ubuntu codename."
            ubuntu_codename=$(. /etc/os-release && echo "$VERSION_CODENAME")
        else
            echo "Error: Cannot determine Ubuntu version codename. 'lsb_release' command not found and /etc/os-release is missing."
            exit 1
        fi
        if [ -z "$ubuntu_codename" ]; then
            echo "Error: Failed to determine Ubuntu version codename."
            exit 1
        fi
        echo "Detected Ubuntu codename: $ubuntu_codename"
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $ubuntu_codename stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        APT_UPDATED_THIS_RUN=""
        echo "Installing Docker Engine, CLI, Containerd, and Docker Compose plugin..."
        install_apt_packages docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        echo "Verifying Docker installation..."
        if command -v docker &> /dev/null && docker --version &> /dev/null; then
            echo "Docker Engine installed successfully: $(docker --version)"
            if docker compose version &> /dev/null; then
                echo "Docker Compose V2 plugin also installed successfully: $(docker compose version)"
            else
                echo "Error: Docker Engine installed, but Docker Compose V2 plugin failed to install or is not recognized."
                exit 1
            fi
        else
            echo "Error: Docker Engine installation failed. Please review the logs above from APT."
            exit 1
        fi
    fi

    local docker_group_message_needed=true
    if [ -n "$SUDO_USER" ]; then
        # Ensure the docker group exists. Create it if it doesn't.
        if ! getent group docker > /dev/null; then
            echo "The 'docker' group does not exist. Attempting to create it..."
            if groupadd docker; then
                echo "Successfully created the 'docker' group."
            else
                echo "Error: Failed to create the 'docker' group. Cannot add user automatically."
            fi
        fi

        # Add the user to the docker group if the group exists and the user is not yet a member.
        if getent group docker > /dev/null; then
            if groups "$SUDO_USER" | grep -qw docker; then
                echo "User '$SUDO_USER' is already a member of the 'docker' group."
                docker_group_message_needed=false
            else
                echo "Attempting to add user '$SUDO_USER' to the 'docker' group..."
                if usermod -aG docker "$SUDO_USER"; then
                    echo "User '$SUDO_USER' has been added to the 'docker' group."
                    echo "IMPORTANT: User '$SUDO_USER' MUST log out and log back in, or run 'newgrp docker',"
                    echo "           for this new group membership to take effect in their current shell sessions."
                    docker_group_message_needed=false
                else
                    echo "Error: Failed to automatically add user '$SUDO_USER' to the 'docker' group."
                fi
            fi
        fi
    else
        echo "Warning: SUDO_USER variable not found. Cannot automatically add to 'docker' group."
    fi

    echo "--- Docker Engine setup and user group check complete ---"
    if [ "$docker_group_message_needed" = true ]; then
        echo "MANUAL ACTION REQUIRED FOR DOCKER PERMISSIONS (if not already set):"
        echo "To run Docker commands as a non-root user (e.g., your user '$SUDO_USER' if applicable, or another user),"
        echo "that user MUST be a member of the 'docker' group."
        echo "If the 'docker' group doesn't exist (unlikely after successful install), create it: sudo groupadd docker"
        echo "Then add the user: sudo usermod -aG docker YOUR_REGULAR_USERNAME"
        echo "After adding the user to the group, they MUST log out and log back in or run 'newgrp docker'"
        echo "for the new group membership to take effect."
    fi
    echo "-------------------------------------------------------------------"
}

# --- Main Setup Logic ---
# 1. Install Prerequisites
ensure_git_installed
ensure_python_installed
check_python_final_version_and_venv
ensure_build_tools_installed
ensure_docker_installed

# Change to the project root directory
cd "$SCRIPT_DIR"
echo "Changed directory to project root: $SCRIPT_DIR"

# 2. Create Virtual Environment (will be initially root-owned)
echo "--- Preparing Python Virtual Environment ('$VENV_DIR') ---"
if [ ! -d "$VENV_DIR" ]; then
    # To prevent 'ensurepip' errors, explicitly install the venv package right before creation.
    echo "Ensuring python${PYTHON_VERSION_STRING}-venv is installed before creating the virtual environment..."
    install_apt_packages "python${PYTHON_VERSION_STRING}-venv"

    echo "Creating Python virtual environment in '$VENV_DIR' using $PYTHON_CMD_TO_USE..."
    if ! "$PYTHON_CMD_TO_USE" -m venv "$VENV_DIR"; then
        echo "Error: Failed to create Python virtual environment." >&2
        echo "This can happen if the 'python${PYTHON_VERSION_STRING}-venv' package is missing or broken." >&2
        echo "The script attempted to install it, but the creation still failed." >&2
        echo "Please check the error messages above and try installing it manually: sudo apt-get install python${PYTHON_VERSION_STRING}-venv" >&2
        exit 1
    fi
    echo "Virtual environment created (initially root-owned)."
else
    echo "Virtual environment '$VENV_DIR' already exists."
fi


# 3. Activate Virtual Environment and Install Dependencies (as root)
echo "Activating virtual environment for this script session (running as root)..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Ensuring pip, setuptools, and wheel are up-to-date in the virtual environment (as root)..."
python -m pip install --upgrade pip setuptools wheel

echo "Installing project dependencies into '$VENV_DIR' (as root)..."
MAIN_REQ_FILE="requirements.txt"
AGENT_REQ_FILE="agent_entrypoint/requirements.txt"
ENV_SERVICE_REQ_FILE="environment_service/requirements.txt"

install_python_requirements_file() {
    local req_file="$1"
    local req_description="$2"
    if [ -f "$req_file" ]; then
        echo "Installing $req_description from '$req_file' (as root)..."
        if ! python -m pip install -r "$req_file"; then
            echo "Error: Failed to install Python requirements from $req_file."
            echo "Please check pip errors above."
            exit 1
        fi
    else
        echo "Warning: $req_description file '$req_file' not found. Skipping."
    fi
}

install_python_requirements_file "$MAIN_REQ_FILE" "core project dependencies"
install_python_requirements_file "$AGENT_REQ_FILE" "agent-specific dependencies"
install_python_requirements_file "$ENV_SERVICE_REQ_FILE" "environment_service dependencies"

echo "All specified Python dependencies installed into '$VENV_DIR'."
deactivate
echo "Deactivated virtual environment for this script session."
echo "----------------------------------------------------------"


# 4. Change Ownership of Virtual Environment to the original sudo user
echo "--- Finalizing Virtual Environment Ownership ---"
if [ -d "$VENV_DIR" ]; then
    if [ -n "$SUDO_USER" ] && [ -n "$SUDO_UID" ] && [ -n "$SUDO_GID" ]; then
        echo "Changing ownership of '$VENV_DIR' and its contents to user '$SUDO_USER' (UID: $SUDO_UID, GID: $SUDO_GID)..."
        if chown -R "$SUDO_UID:$SUDO_GID" "$VENV_DIR"; then
            echo "Ownership of '$VENV_DIR' successfully changed to '$SUDO_USER'."
        else
            echo "Error: Failed to change ownership of '$VENV_DIR' to $SUDO_USER."
            echo "You may need to manually run: sudo chown -R $SUDO_USER:$SUDO_USER '$VENV_DIR'"
        fi
    else
        echo "Warning: SUDO_USER, SUDO_UID, or SUDO_GID not set. Cannot automatically change ownership of '$VENV_DIR'."
        echo "The virtual environment '$VENV_DIR' and its contents are likely still owned by root."
        echo "You will need to manually change ownership: sudo chown -R YOUR_USERNAME:YOUR_GROUP '$VENV_DIR'"
    fi
else
    echo "Error: Virtual environment '$VENV_DIR' not found after dependency installation. Cannot change ownership."
fi
echo "----------------------------------------------"


# 5. Remind about config.py for AI API Key
echo ""
echo "--- Configuration Reminder ---"
CONFIG_PY_PATH="config.py"
if [ ! -f "$CONFIG_PY_PATH" ]; then
    echo "IMPORTANT: Please create a '$CONFIG_PY_PATH' file in the project root ('$SCRIPT_DIR') with your 'AI' API key."
    echo "As a regular user, create this file. Example content for $CONFIG_PY_PATH:"
    echo ""
    echo "# $CONFIG_PY_PATH"
    echo "AI_API_KEY = \"YOUR_ACTUAL_AI_API_KEY\""
    echo "# DEBUG_TIMER_SECONDS = 25 # Optional: for timed auto-shutdown during 'run.py up'"
    echo ""
    echo "This file is gitignored (ensure it is!) and is necessary for LLM features."
else
    echo "'$CONFIG_PY_PATH' already exists. Ensure it contains your AI_API_KEY if you plan to use LLM features."
fi

# 6. Final Instructions (Updated)
echo ""
echo "--- Setup Complete (as root execution finished) ---"
VENV_OWNERSHIP_MESSAGE_SET=false
if [ -n "$SUDO_USER" ]; then
    if [ -d "$VENV_DIR" ] && [ "$(stat -c '%U' "$VENV_DIR")" = "$SUDO_USER" ]; then
        echo "The Python virtual environment '$VENV_DIR' is now owned by user '$SUDO_USER'."
        VENV_OWNERSHIP_MESSAGE_SET=true
    fi
fi
if [ "$VENV_OWNERSHIP_MESSAGE_SET" = false ]; then
    echo "Warning: Ownership of the Python virtual environment '$VENV_DIR' might still be root"
    echo "(e.g., if SUDO_USER was not detected or chown failed)."
    echo "If so, you may need to manually change its ownership (e.g., sudo chown -R YOUR_USERNAME:YOUR_GROUP '$VENV_DIR')"
    echo "or use 'sudo' to activate it."
fi

echo ""
echo "To activate the virtual environment:"
echo "  cd $SCRIPT_DIR"
echo "  source $VENV_DIR/bin/activate"
echo ""

# Docker group message
if [ -n "$SUDO_USER" ]; then
    if groups "$SUDO_USER" | grep -qw docker; then
        echo "User '$SUDO_USER' is part of the 'docker' group."
        echo "If this group membership was just added by this script, you MUST log out and log back in"
        echo "or run 'newgrp docker' in your new terminal session for it to take effect before running Docker commands without sudo."
    else
        # This case implies SUDO_USER was found, but they are not in docker group (and usermod might have failed or was not applicable)
        echo "User '$SUDO_USER' may not be in the 'docker' group, or the automatic addition failed."
        echo "To run Docker commands (like those in 'run.py') without sudo, user '$SUDO_USER' must be in the 'docker' group."
        echo "If not already handled, you may need to run: sudo usermod -aG docker $SUDO_USER"
        echo "Then, log out and log back in or run 'newgrp docker'."
    fi
else
    # SUDO_USER not found case
    echo "Regarding Docker permissions: your regular user will need to be in the 'docker' group"
    echo "to run 'python run.py' (which executes Docker commands) without sudo."
    echo "Example: sudo usermod -aG docker YOUR_USERNAME (then log out/in or run 'newgrp docker')."
fi
echo ""
echo "Note: Project files in '$SCRIPT_DIR' that you created (not by this script as root)"
echo "should retain their original ownership."
echo "------------------------"
