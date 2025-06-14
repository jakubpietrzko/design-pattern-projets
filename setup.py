"""Script containing functions for managing the project workspace.

Available functions and corresponding arguments are described in the
main function as well as in the doc strings of the functions.
"""

import argparse
import pathlib
import venv
from os import path
import pip
import models
import config

HOME_PATH = pathlib.Path(__file__).absolute().parent.as_posix()

def migrate():
    models_num = len(models.model_list)
    print(f"migrating {models_num} model{'s' if models_num > 1 else ''} to {config.DATABASE_PATH} ...")
    for model in models.model_list:
        try:
            model.migrate()
        except Exception as e:
            print(f'Error during migrating model {model}: {e}')
            return

    print('All models migrated succesfully')


def setup_venv() -> None:
    """Sets up the virtual environment."""

    venv_path = path.join(HOME_PATH, "venv")

    venv.create(venv_path, with_pip=True, upgrade_deps=True)

    print(f"Successfully created a virtual environment at directory '{venv_path}'")
    print("You can now activate the environment with 'source ./venv/bin/activate'.")
    print("Then type 'python3 -m pip install -r requirements.txt' to install dependencies.")
    print("Then type 'deactivate' to deactivate the environment.")


def main(function: str, *args) -> None:
    """Main function delegating the flow to other ones.

    Args:
        function (str): Name of the function to be called.
    """
    for callable in [setup_venv, migrate]:
        if callable.__name__ == function:
            callable(*args)
            return
        
    raise RuntimeError(f"Couldn't find the function '{function}'.")


if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description="Available functions:\tsetup_venv")

    arg_parser.add_argument("function_name", help="name of the function to be used")
    arg_parser.add_argument("args", nargs='*', help="positional arguments for the function")

    args = arg_parser.parse_args()

    main(args.function_name, *args.args)