from fastapi import HTTPException, status


class RecordNotFoundError(HTTPException):
    """Raised when a record is not found in the database."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class RecordAlreadyExistsError(HTTPException):
    """Raised when trying to create a record that already exists."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InvalidRecordError(Exception):
    """
    Exception raised when a record is invalid
    (e.g. missing required fields, invalid field values).
    """


class DeleteError(HTTPException):
    """Raised when there is an error deleting a record."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
