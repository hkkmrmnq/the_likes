class Error(Exception):
    """Base exception with required message"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFound(Error):
    def __init__(self, message: str = 'Item not found.'):
        super().__init__(message)


class InactiveUser(Error):
    def __init__(
        self,
        message: str = 'User account is deactivated.',
    ):
        super().__init__(message)


class Forbidden(Error):
    def __init__(
        self,
        message: str = 'Acces forbidden.',
    ):
        super().__init__(message)


class Unauthorized(Error):
    def __init__(
        self,
        message: str = 'Unauthorized.',
    ):
        super().__init__(message)


class AlreadyExists(Error):
    def __init__(
        self,
        message: str = 'Already exists.',
    ):
        super().__init__(message)


class BadRequest(Error):
    def __init__(
        self,
        message: str = 'Bad request.',
    ):
        super().__init__(message)


class IncorrectDefinitions(Error):
    def __init__(
        self,
        message: str = "Data in db don't match Basic data.xlsxx",
    ):
        super().__init__(message)


class ServerError(Error):
    def __init__(
        self,
        message: str = 'Something went wrong. Contact us.',
    ):
        super().__init__(message)
