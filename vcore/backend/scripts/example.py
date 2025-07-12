from typing import Any

from vcore.backend.services.scripts import Script, ScriptOutput


class ExampleScript(Script):
    """
    This example inputs a number and doubles it.

    """

    def _validate_input(self, num: Any) -> bool:
        if not num:
            raise ValueError("Script Validation Error: A input value is required for `num`.")

        if not isinstance(num, int):
            raise ValueError("Script Validation Error: `num` must be an integer.")

        if num < 0:
            raise ValueError("Script Validation Error: `num` must be greater than 0.")

        return True

    def _run(self, num: int) -> ScriptOutput:  # noqa: F821
        return ScriptOutput(
            success=True,
            message=f"The number {num} doubled is {num * 2}.",
            data={"doubled_num": num * 2},
        )
