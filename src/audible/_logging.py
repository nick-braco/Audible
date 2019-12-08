import logging
import pathlib
import warnings
from logging.handlers import RotatingFileHandler
from typing import Union, Optional


LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
    'not_set': logging.NOTSET
}

log_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s [%(name)s] %(filename)s:%(lineno)d: %(message)s'
)


class LogHelper:
    """Helper class to setup logging"""
    def __init__(self, logger_name: str = 'audible', *,
                 level: Optional[Union[str, int]] = None,
                 capture_warnings: bool = None) -> None:

        self.logger = logging.getLogger(logger_name)
        self.set_global_level(level) if level else None
        self.capture_warnings(capture_warnings) if capture_warnings else None

    @staticmethod
    def capture_warnings(target: bool = True) -> None:
        """
        This method is used to turn the capture of warnings
        by logging on and off
        """
        logging.captureWarnings(target)

    def set_global_level(self, level: Union[str, int]) -> None:
        """Sets the threshold for main logger to level"""
        self._set_level(self.logger, level)

    def _set_handler(self, handler, formatter, name, level):
        handler.setFormatter(formatter)
        handler.set_name(name)
        self._set_level(handler, level) if level else None
        self.logger.addHandler(handler)

    def _set_level(self, handler, level: Union[str, int]) -> None:
        if isinstance(level, str):
            level = level.lower().strip()
            level = LEVELS.get(level, logging.NOTSET)

        handler.setLevel(level)
        handler_level_name = logging.getLevelName(handler.level)
        self.logger.info(
            f'set logging threshold for {handler.name} to {handler_level_name}'
        )
        if handler.level < self.logger.level or self.logger.level == 0:
            warnings.warn(
                (f'logging threshold for {handler.name} lower than '
                 f'logging threshold for global logger')
            )

    def set_console_logger(self, level: Optional[Union[str, int]] = None,
                           formatter: logging.Formatter = log_formatter
                           ) -> None:
        """
        Add stream handler to main logger and optional set threshold to level
        """
        handler = logging.StreamHandler()
        self._set_handler(handler=handler, formatter=formatter,
                          name='ConsoleLogger', level=level)

    def set_file_logger(self, filename: str,
                        level: Optional[Union[str, int]] = None,
                        formatter: logging.Formatter = log_formatter,
                        encoding: str = 'utf8',
                        **kwargs
                        ) -> None:
        """
        Add file handler to main logger and optional set threshold to level
        """
        try:
            filename = pathlib.Path(filename)
        except NotImplementedError:
            filename = pathlib.WindowsPath(filename)

        handler = logging.FileHandler(filename, encoding=encoding, **kwargs)
        self._set_handler(handler=handler, formatter=formatter,
                          name='FileLogger', level=level)

    def set_rotating_file_logger(self, filename: str,
                                 level: Optional[Union[str, int]] = None,
                                 formatter: logging.Formatter = log_formatter,
                                 max_bytes: int = (1024*1024),
                                 backup_count: int = 5,
                                 encoding: str = 'utf8',
                                 **kwargs
                                 ) -> None:
        """
        Add rotating file handler to main logger and
        optional set threshold to level
        """
        try:
            filename = pathlib.Path(filename)
        except NotImplementedError:
            filename = pathlib.WindowsPath(filename)
    
        handler = RotatingFileHandler(
            filename=filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
            **kwargs
        )
        self._set_handler(handler=handler, formatter=formatter,
                          name='RotatingFileLogger', level=level)

    def set_custom_logger(self, handler, name, level=None,
                          formatter: logging.Formatter = log_formatter
                          ) -> None:
        """
        Add custom logging handler to main logger and optional
        set threshold to level
        """
        self._set_handler(handler=handler, formatter=formatter,
                          name=name, level=level)
