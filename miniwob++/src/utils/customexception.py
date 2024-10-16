
class CustomException(Exception):
    def __init__(self, message):
        print(f"[CustomException] :: {message}")
        super().__init__(message)


class ElementNotFoundError(Exception):
    def __init__(self, message: str = 'Element Not Found!'):
        Exception.__init__(self, message)
