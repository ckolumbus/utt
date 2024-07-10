import argparse
import datetime
import importlib
import os
from typing import NamedTuple, Optional

from utt.report.azdo.wi import AzdoWiQuery
from utt.report.sql.model import SqlModel

from ..api import _v1
from ..components.report_args import ReportArgs
from ..report import formatter


class TagReportArgs(NamedTuple):
    tag_name_filter: Optional[str]


def tagreport_args(args: argparse.Namespace) -> TagReportArgs:

    return TagReportArgs(tag_name_filter=args.tag)


_v1.register_component(TagReportArgs, tagreport_args)


class TagReportView(_v1.ReportView):
    def __init__(self, sql: SqlModel, report_args: ReportArgs, tagreport_args: TagReportArgs, azdo_wi: AzdoWiQuery):
        self._sql = sql
        self._report_args = report_args
        self._tagreport_args = tagreport_args
        self._azdo_wi = azdo_wi

    def render(self, output: _v1.Output) -> None:
        print(file=output)
        print(formatter.title("SQL Tags"), file=output)
        print(file=output)

        c = self._sql.get_cursor()

        where_condition = "type = ?"
        if self._tagreport_args.tag_name_filter:
            # TODO: SQL Injection !!!!
            where_condition += f" AND tag = '{self._tagreport_args.tag_name_filter}'"

        if self._report_args.project_name_filter:
            # TODO: SQL Injection !!!!
            where_condition += f" AND project = '{self._report_args.project_name_filter}'"

        query = (
            "SELECT time(sum(duration), 'unixepoch'), tags.tag as tag, tags.value as tagvalue,"
            "group_concat(DISTINCT project) as projects "
            "FROM   activities "
            "INNER JOIN tags on tags.tagact = activities.actid "
            "WHERE {condition} "
            "GROUP BY (tags.tag || ':' || tags.value)"
            ";"
        ).format(condition=where_condition)

        query_sum = "SELECT time(sum(duration), 'unixepoch')" "FROM   activities " "WHERE  type = ? " ";"

        c.execute(query_sum, (_v1.Activity.Type.WORK,))
        work_sum = c.fetchone()[0]

        c.execute(query, (_v1.Activity.Type.WORK,))
        rows = c.fetchall()

        for r in rows:
            if r[1] == "w":
                r += (self._azdo_wi.get_work_item(int(r[2])),)
            print(r, file=output)

        print(file=output)
        print(f"Work sum: {work_sum}", file=output)


_v1.register_component(TagReportView, TagReportView)


class TagReportHandler:
    def __init__(self, sql_model: SqlModel, output: _v1.Output, tagreport_view: TagReportView):
        self._model = sql_model
        self._output = output
        self._tagreport_view = tagreport_view

    def __call__(self):
        self._tagreport_view.render(self._output)


# reuse report plugin
def add_args(parser: argparse.ArgumentParser):
    m = importlib.import_module("utt.plugins.0_report")

    parser.add_argument(
        "--tag", default=None, type=str, help="Show activities only for the specified tag type.",
    )

    m.add_args(parser)


tagreport_command = _v1.Command("tags", "Summarize tags for given time period", TagReportHandler, add_args)

_v1.register_command(tagreport_command)
