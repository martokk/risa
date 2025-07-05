from app import logger


def convert_risa_rsync_options_to_text(
    env_name: str,
    queue_name: str,
    source_env: str,
    source_loc: str,
    dest_env: str,
    dest_loc: str,
    option_u: bool,
    option_ignore_existing: bool,
) -> str:
    """
    Convert Risa rsync options to text.

    Args:
        env_name: The environment name.
        queue_name: The queue name.
        source_env: The source environment.
        source_loc: The source location.
        dest_env: The destination environment.
        dest_loc: The destination location.
        option_u: The option u.
        option_ignore_existing: The option ignore existing.

    Returns:
        The text of the rsync command.
    """

    action = "push" if source_env == env_name else "pull"

    return f"Job on r|{env_name.upper()} to {action.upper()} [{source_env}]`{source_loc}` to [{dest_env}]`{dest_loc}`"


def generate_rsync_command_job(
    env_name: str,
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

    rsync -rtvzP --ignore-existing source/ dest/
    rsync -tvzP
    rsync -e "ssh -i ~/.ssh/id_rsync_script" -avz /local/path/ user@remote:/remote/path/
    """
    user = "martokk"
    ssh_key_path = f"~/.ssh/id_risa_{env_name.lower()}"
    remote = "999.999.999.999"
    _user_at_remote = f"{user}@{remote}"
    action = "push" if source_env == env_name else "pull"

    # Start building the command.
    command = f'rsync -e "ssh -i {ssh_key_path}" -tvzP'

    if option_recursive:
        command += " -r"
    if option_u:
        command += " -u"
    elif option_ignore_existing:
        command += " --ignore-existing"

    if action == "push":
        if destination_env == "local":
            raise ValueError(
                "Destination environment cannot be 'local' when pushing. A remote server can not connect to 'http://localhost' to push to."
            )
        command += f" {source_location} {_user_at_remote}:{destination_location}"
    else:
        if source_env == "local":
            raise ValueError(
                "Source environment cannot be 'local' when pulling. A remote server can not connect to 'http://localhost' to pull from."
            )
        command += f" {_user_at_remote}:{source_location} {destination_location}"

    logger.debug(f"command: {command}")
    return command
