from app import crud, logger
from framework.core.db import get_db_context


def convert_risa_rsync_options_to_text(
    env_name: str,
    queue_name: str,
    source_env: str,
    source_location: str,
    destination_env: str,
    destination_location: str,
    option_u: bool,
    option_ignore_existing: bool,
) -> str:
    """
    Convert Risa rsync options to text.

    Args:
        env_name: The environment name.
        queue_name: The queue name.
        source_env: The source environment.
        source_location: The source location.
        destination_env: The destination environment.
        destination_location: The destination location.
        option_u: The option u.
        option_ignore_existing: The option ignore existing.

    Returns:
        The text of the rsync command.
    """

    action = "push" if source_env == env_name else "pull"

    return f"Job on r|{env_name.upper()} to {action.upper()} [{source_env}]`{source_location}` to [{destination_env}]`{destination_location}`"  # noqa: E501


def generate_rsync_command_job(
    job_env: str,
    source_env: str,
    source_location: str,
    destination_env: str,
    destination_location: str,
    option_u: bool = False,
    option_ignore_existing: bool = False,
    option_recursive: bool = False,
) -> str:
    """
    Generate a rsync command job.

    rsync -e "ssh -i ~/.ssh/id_risa_dev -p 40196  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" -tvzP -r -u root@213.192.2.73:/workspace/__OUTPUTS__/risa/ /media/martokk/FILES/AI/__INBOX__/risa/

    ---
    Generate keys: `ssh-keygen -t ed25519 -f ~/.ssh/id_risa_dev -C "risa@dev"`

    """  # noqa: E501

    action = "push" if source_env == job_env else "pull"

    # Lookup the environment state from the database.
    lookup_env = destination_env if action == "push" else source_env

    with get_db_context() as db:
        env_state = crud.instance_state.sync.get(db, id=lookup_env)
    if not env_state:
        raise ValueError(f"Environment {lookup_env} not found")

    # Determine the user, host, and port to use for the rsync command.
    user = None
    host = None
    port = None
    ssh_dir_path = "~/.ssh"
    if env_state.id == "playground":
        user = "root"
        host = env_state.public_ip
        port = env_state.runpod_tcp_port_22
    elif env_state.id == "host":
        user = "ubuntu"
        host = env_state.public_ip
    elif env_state.id == "local":
        ssh_dir_path = "/root/.ssh"

    _user_at_remote = f"{user}@{host}"

    # Determine the ssh key path to use for the rsync command.
    ssh_key_path = f"{ssh_dir_path}/id_risa_{job_env.lower()}"

    # Start building the command.
    ssh_command = f"ssh -i {ssh_key_path} {'-p ' + str(port) if port else ''} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"  # noqa: E501
    command = f'rsync -e "{ssh_command}" -tvzP'

    # Add the options to the command.
    if option_recursive:
        command += " -r"
    if option_u:
        command += " -u"
    elif option_ignore_existing:
        command += " --ignore-existing"

    # Add the source and destination to the command.
    if action == "push":
        if destination_env == "local":
            raise ValueError(
                "Destination environment cannot be 'local' when pushing. A remote server can not connect to 'http://localhost' to push to."  # noqa: E501
            )
        command += f" {source_location} {_user_at_remote}:{destination_location}"
    else:
        if source_env == "local":
            raise ValueError(
                "Source environment cannot be 'local' when pulling. A remote server can not connect to 'http://localhost' to pull from."  # noqa: E501
            )
        command += f" {_user_at_remote}:{source_location} {destination_location}"

    logger.debug(f"command: {command}")
    return command
