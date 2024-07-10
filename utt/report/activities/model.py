import itertools
from datetime import timedelta
from typing import Dict, List

from ...data_structures.activity import Activity
from .. import formatter
from ..common import filter_activities_by_type


class ActivitiesModel:
    def __init__(self, activities: List[Activity]):
        self.names_work = _groupby_name(filter_activities_by_type(activities, Activity.Type.WORK))
        self.names_break = _groupby_name(filter_activities_by_type(activities, Activity.Type.BREAK))


def _groupby_name(activities: List[Activity]) -> List[Dict]:
    def key(act):
        return act.name.name

    result = []
    sorted_activities = sorted(activities, key=key)
    activities_sum = sum((act.duration for act in activities), timedelta())

    for _, activities in itertools.groupby(sorted_activities, key):
        activities = list(activities)
        project = activities[0].name.project
        s = sum((act.duration for act in activities), timedelta())
        result.append(
            {
                "project": project,
                "duration": "{:5.1%}".format(s/activities_sum),
                "duration_full": formatter.format_duration(s) + " - {:5.1%}".format(s/activities_sum),
                "name": ", ".join(sorted(set(act.name.task for act in activities))),
            }
        )

    return sorted(result, key=lambda act: (act["project"].lower(), act["name"].lower()))
