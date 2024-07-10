import datetime
import itertools
from typing import Dict, List

from ...data_structures.activity import Activity
from .. import formatter
from ..common import filter_activities_by_type


class ProjectsModel:
    def __init__(self, activities: List[Activity]):
        self.projects = groupby_project(filter_activities_by_type(activities, Activity.Type.WORK))


def duration(activities: List[Activity]) -> datetime.timedelta:
    return sum((act.duration for act in activities), datetime.timedelta())

def groupby_project(activities: List[Activity]) -> List[Dict]:
    def key(act):
        return act.name.project

    result = []
    sorted_activities = sorted(activities, key=key)
    activities_sum = sum((act.duration for act in activities), datetime.timedelta())

    for project, activities in itertools.groupby(sorted_activities, key):
        activities = list(activities)
        s = sum((act.duration for act in activities), datetime.timedelta())
        result.append(
            {
                "duration": formatter.format_duration(s),
                "duration_ratio": "{:5.1%}".format(s/activities_sum),
                "duration_full": formatter.format_duration(s) + " - {:5.1%}".format(s/activities_sum),
                "project": project,
                "name": ", ".join(
                    sorted(
                        set(act.name.task for act in activities),
                        key=lambda task: task.lower(),
                    )
                ),
            }
        )

    return sorted(result, key=lambda result: result["project"].lower())
