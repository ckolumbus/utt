import os
import re

import argparse
import importlib

from string import Formatter
from datetime import timedelta

from typing import NamedTuple, Optional

from utt.report.azdo.wi import AzdoWiQuery
from utt.report.sql.model import SqlModel

from ..api import _v1
from ..components.report_args import ReportArgs
from ..report import formatter

WORKTIEM_QUERY_TAG = "w"

class TagReportArgs(NamedTuple):
    tag_name_filter: Optional[str]


def tagreport_args(args: argparse.Namespace) -> TagReportArgs:

    return TagReportArgs(tag_name_filter=args.tag)


_v1.register_component(TagReportArgs, tagreport_args)


# ----------------------------------------------
# https://stackoverflow.com/a/4628148
# ----------------------------------------------
regex = re.compile(r'((?P<hours>\d+?):)?((?P<minutes>\d+?):)?((?P<seconds>\d+?))?')


def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)
# ----------------------------------------------

# ----------------------------------------------
# https://stackoverflow.com/a/42320260
# ----------------------------------------------
def strfdelta(tdelta, fmt='{H}:{M:02}:{S:02}', inputtype='timedelta'):
    """Convert a datetime.timedelta object or a regular number to a custom-
    formatted string, just like the stftime() method does for datetime.datetime
    objects.

    The fmt argument allows custom formatting to be specified.  Fields can 
    include seconds, minutes, hours, days, and weeks.  Each field is optional.

    Some examples:
        '{D:02}d {H:02}h {M:02}m {S:02}s' --> '05d 08h 04m 02s' (default)
        '{W}w {D}d {H}:{M:02}:{S:02}'     --> '4w 5d 8:04:02'
        '{D:2}d {H:2}:{M:02}:{S:02}'      --> ' 5d  8:04:02'
        '{H}h {S}s'                       --> '72h 800s'

    The inputtype argument allows tdelta to be a regular number instead of the  
    default, which is a datetime.timedelta object.  Valid inputtype strings: 
        's', 'seconds', 
        'm', 'minutes', 
        'h', 'hours', 
        'd', 'days', 
        'w', 'weeks'
    """
    
    # Convert tdelta to integer seconds.
    if inputtype == 'timedelta':
        remainder = int(tdelta.total_seconds())
    elif inputtype in ['s', 'seconds']:
        remainder = int(tdelta)
    elif inputtype in ['m', 'minutes']:
        remainder = int(tdelta)*60
    elif inputtype in ['h', 'hours']:
        remainder = int(tdelta)*3600
    elif inputtype in ['d', 'days']:
        remainder = int(tdelta)*86400
    elif inputtype in ['w', 'weeks']:
        remainder = int(tdelta)*604800

    f = Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ('W', 'D', 'H', 'M', 'S')
    constants = {'W': 604800, 'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)

# ----------------------------------------------


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
            "SELECT sum(duration), tags.tag as tag, tags.value as tagvalue,"
            "group_concat(DISTINCT project) as projects "
            "FROM   activities "
            "INNER JOIN tags on tags.tagact = activities.actid "
            "WHERE {condition} "
            "GROUP BY (tags.tag || ':' || tags.value)"
            ";"
        ).format(condition=where_condition)

        query_sum = ( 
            "SELECT sum(duration) "
            "FROM   activities "
            "WHERE  type = ? " 
            ";"
        )

        c.execute(query_sum, (_v1.Activity.Type.WORK,))
        # duration stored in seconds 
        work_sum =  timedelta(seconds=int(c.fetchone()[0]))

        c.execute(query, (_v1.Activity.Type.WORK,))
        rows = c.fetchall()
        cond_sum = timedelta(0)
        for r in rows:
            if r[1] == WORKTIEM_QUERY_TAG:
                r += (self._azdo_wi.get_work_item(int(r[2])),)
            # duration stored in seconds 
            cond_sum += timedelta(seconds=int(r[0]))
            print(f"{strfdelta(timedelta(seconds=int(r[0]))):>12} {r[1]:<4}: {r[2]}", file=output)

        print(file=output)
        print(f"Aggregate Tag Sum (incl. double counts): {strfdelta(cond_sum):>12}" , file=output) 
        print(f"Total work in time range               : {strfdelta(work_sum):>12}", file=output)


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
