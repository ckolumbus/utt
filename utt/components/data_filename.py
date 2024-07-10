import argparse
import os
import typing

from ..constants import ENTRY_FILENAME, DATA_FILE_NAME_ENVVAR
from .data_dirname import DataDirname

DataFilename = typing.NewType("DataFilename", str)


def data_filename(args: argparse.Namespace, data_dirname: DataDirname) -> DataFilename:
    if args.data_filename:
        return args.data_filename

    if DATA_FILE_NAME_ENVVAR in os.environ:
        data_filename = os.environ[DATA_FILE_NAME_ENVVAR]
        return data_filename

    return DataFilename(os.path.join(data_dirname, ENTRY_FILENAME))
