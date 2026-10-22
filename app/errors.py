class ValidationError(Exception):
    """Invalid user input. `errors` maps field name -> message."""

    def __init__(self, errors):
        super().__init__("validation failed")
        self.errors = errors


class NotFoundError(Exception):
    pass


class ServiceError(Exception):
    """Generic failure; message is safe to show to users (SEC-12)."""
