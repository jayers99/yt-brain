class YtbrainError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class VideoNotFoundError(YtbrainError):
    pass


class ConfigError(YtbrainError):
    pass


class IngestError(YtbrainError):
    pass


class DatabaseError(YtbrainError):
    pass
