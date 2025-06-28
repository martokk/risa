from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from app.services.a1111_wrapper import RisaA1111Wrapper, Text2ImgSettings


class ScriptOutput(BaseModel):
    success: bool | None = None
    message: str | None = None
    data: Any | None = None


class Script(BaseModel):
    # Input (Any or None)

    # Output
    output: ScriptOutput | None = None

    # Run
    @abstractmethod
    def _validate_input(self, *args: Any, **kwargs: Any) -> bool:
        pass

    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> ScriptOutput:
        pass

    def run(self, *args: Any, **kwargs: Any) -> ScriptOutput:
        if not self._validate_input(*args, **kwargs):
            raise ValueError("Script input validation failed.")

        self.output = self._run(*args, **kwargs)
        return self.output
