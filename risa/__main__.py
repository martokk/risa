# import typer
# from loguru import logger
# from rich.console import Console

# from risa import version
# from example import ExampleClass

# # Configure Loguru Logger
# logger.add("log.log", level="TRACE", rotation="50 MB")

# # Configure Rich Console
# console = Console()

# # Configure Typer
# app = typer.Typer(
#     name="risa",
#     help="A python project created by Martokk.",
#     add_completion=False,
# )


# # Print Current Version
# def version_callback(print_version: bool) -> None:
#     """Print the version of the package."""
#     if print_version:
#         console.print(f"[yellow]risa[/] version: [bold blue]{version}[/]")
#         raise typer.Exit()


# # Typer Commands
# @app.command()
# def main(
#     profile: str = typer.Option(..., help="Profile to load."),
#     print_version: bool = typer.Option(
#         None,
#         "-v",
#         "--version",
#         callback=version_callback,
#         is_eager=True,
#         help="Prints the version of the risa package.",
#     ),
# ) -> None:

#     # Example Entry Point
#     console.print(ExampleClass().print_name(name="Ron Paul"))
#     logger.info(f"Example Entry Point! {profile=}")

#     # Example #DIV/0 Logging Error (caught by @logger.catch decorator)
#     ExampleClass().example_divide_by_zero()


# if __name__ == "__main__":
#     app()

#####################################################################################

from typing import Dict

import argparse

from risa.common.profiles import Profile, Profiles
from risa.common.utils import ViewMixIn
from risa.stats.stats import Stats
from risa.telegram_bots.main import run_all_telegram_bots

parser = argparse.ArgumentParser()
# parser.add_argument("-u", "--update", action="store_true",
#                     help="Checks for new updates and adds them to the feed")
# parser.add_argument("-f", "--feed", action="store_true",
#                     help="Displays the feed")
parser.add_argument(
    "--pull_service", type=str, help="Pull all expanded urls for provided service_name."
)
parser.add_argument("-t", "--run_telegram_bots", action="store_true", help="Runs Telegram Bots")
parser.add_argument(
    "-e", "--print_errors", action="store_true", help="Prints all errors and warnings."
)
parser.add_argument("-s", "--print_stats", action="store_true", help="Prints all stats")
parser.add_argument("--print_stat", type=str, help="Prints single stat details.")
args = parser.parse_args()


class RisaView(ViewMixIn):
    @staticmethod
    def print_profiles(profiles: list) -> None:
        for profile in profiles:
            print(f"{profile.profile_type}: {profile.name_or_folder}")

    def print_user_yaml_errors(self, profiles: Profiles) -> None:
        for profile in profiles:
            if profile.validation.found_issues:
                self.print_profile_errors(profile=profile)

    @staticmethod
    def print_profile_errors(profile: Profile):
        print(f"Profile: {profile.name_or_folder} ({profile.profile_type})")
        if profile.validation.found_errors:
            for error in profile.validation.errors:
                print(f"\t- Error: {error}")
        if profile.validation.found_warnings:
            for warning in profile.validation.warnings:
                print(f"\t- Warning: {warning}")

    @staticmethod
    def print_stats(stats_text) -> None:
        print(stats_text)

    @staticmethod
    def print_stat(stat_text) -> None:
        print(stat_text)


class Risa:
    def __init__(self) -> None:
        self.view = RisaView()
        self.profiles = Profiles()

    def main(self) -> None:
        self.view.print_horizontal_line()

        print(f"Total Profiles: {self.profiles.__len__()}")
        self.view.print_horizontal_line()
        self.print_errors()
        self.view.print_horizontal_line()

        self.view.print_profiles(profiles=self.profiles)
        self.view.print_horizontal_line()

    def pull_service(self, attribute: str) -> Dict:
        return self.profiles.get_by_attribute(attribute=attribute)

    def print_service(self, attribute: str) -> None:
        data = self.pull_service(attribute=attribute)
        for profile_name, attribute_data in data.items():
            print(f"{profile_name}: {attribute_data}")

    def print_errors(self) -> None:
        self.view.print_user_yaml_errors(profiles=self.profiles)

    def print_stats(self) -> None:
        self.view.print_stats(stats_text=Stats().summary_text)

    def print_stat(self, id_name: str) -> None:
        self.view.print_stat(stat_text=Stats().get_view_details_text(id_name=id_name))

    def run_telegram_bots(self) -> None:
        run_all_telegram_bots()


def arg_router() -> None:
    risa = Risa()
    if args.print_errors:
        risa.print_errors()
    if args.pull_service:
        risa.print_service(args.pull_service)
    if args.print_stats:
        risa.print_stats()
    if args.print_stat:
        risa.print_stat(id_name=args.print_stat)
    if args.run_telegram_bots:
        risa.run_telegram_bots()


if __name__ == "__main__":
    if args:
        print(args)
        arg_router()
    else:
        # Risa().main()
        Risa().run_telegram_bots()

    # risa = Risa()
    # risa.print_data('twitter')
    # risa.print_data('manyvids')
