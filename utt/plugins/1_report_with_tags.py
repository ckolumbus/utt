import datetime
import itertools
from collections import defaultdict
from typing import Dict, List

from utt.api import _v1
from utt.report.azdo.wi import AzdoWiQuery

from ..components.report_args import ReportArgs
from ..components.output import Output
from ..data_structures.activity import Activity
from ..report import formatter
from ..report.common import filter_activities_by_type, print_dicts


class TagSummaryModel:
    def __init__(self, activities: List[Activity]):
        self._activities = activities
        self.tags = groupby_tag(filter_activities_by_type(activities, Activity.Type.WORK))


def groupby_tag(activities: List[Activity]) -> List[Dict]:

    result = defaultdict(lambda: {"key": "", "value": "", "duration": datetime.timedelta(0), "ratio": 0})
    activities_sum = sum((act.duration for act in activities), datetime.timedelta())

    for act in activities:
        if act.tags:
            for tag in act.tags:
                key = f"{tag[0]}:{tag[1]}"
                result[key]["duration"] += act.duration
                result[key]["ratio"] += act.duration/activities_sum
                result[key]["tag"] = tag[0]
                result[key]["value"] = tag[1]

    return dict(result)


_v1.register_component(TagSummaryModel, TagSummaryModel)


class TagSummarySubView:
    def __init__(self, model: TagSummaryModel, azdo: AzdoWiQuery, detailed: bool = False):
        self._detailedReport = detailed
        self._model = model
        self._azdo = azdo

    def print_tags(self, dcts: Dict[str, Dict], output: Output) -> None:
        format_string = "({duration_fmt} - {ratio:5.1%}) {tag:<{tag_max_length}}: {value} {wi}"
        if (not self._detailedReport):
            format_string = "({ratio:5.1%}) {tag:<{tag_max_length}}: {value} {wi}"

        tag_max_length = max(itertools.chain([0], (len(dcts[key]["tag"]) for key in dcts)))
        for key in dict(sorted(dcts.items(), key=lambda item: item[0])):
            if (not self._detailedReport):
                if (dcts[key]["tag"] not in ["t", "w", "adhoc"]):
                    continue
            dct = dcts[key]
            context = {"tag_max_length": tag_max_length}

            context["wi"] = ""
            context["duration_fmt"] = formatter.format_duration(dct["duration"]) 
            if dct["tag"] == "w":
                context["wi"] = " (" + self._azdo.get_work_item(int(dct["value"])) + ")"

            print(format_string.format(**dict(context, **dct)), file=output)

    def render(self, output: Output) -> None:
        print(file=output)
        print(formatter.title("Tags"), file=output)
        print(file=output)

        self.print_tags(self._model.tags, output)


# -------------------------------------------------------------------------------------------
class MySubModel:
    def __init__(self, activities: _v1.Activities,  report_args: ReportArgs):
        self._report_range = report_args.range
        self._activities = activities

    @property
    def activity_count(self):
        return len(self._activities)

    @property
    def report_range(self):
        return self._report_range


_v1.register_component(MySubModel, MySubModel)


class MySubView:
    def __init__(self, model: MySubModel ):
        self._model = model

    def render(self, output: _v1.Output) -> None:

        print(file=output)
        date_str = format_date(self._model.report_range.start)
        if self._model.report_range.start != self._model.report_range.end:
            date_str = " ".join([date_str, "to", format_date(self._model.report_range.end)])
        print(formatter.title(date_str), file=output)
        print(file=output)
        print(f"Number of activities: {self._model.activity_count}", file=output)


def format_date(date: datetime.date) -> str:
    return date.strftime("%A, %b %d, %Y (week {week})".format(week=date.isocalendar()[1]))

# -------------------------------------------------------------------------------------------


class MyReportView(_v1.ReportView):
    def __init__(
        self,
        report_model: _v1.ReportModel,
        my_sub_model: MySubModel,
        my_tag_model: TagSummaryModel,
        azdo_wi: AzdoWiQuery,
    ):
        self._report_model = report_model
        self._my_sub_model = my_sub_model
        self._my_tag_model = my_tag_model
        self._my_azdo_wi = azdo_wi

    def render(self, output: _v1.Output) -> None:

        if self._report_model.args.show_details:
            _v1.SummaryView(self._report_model.summary_model).render(output)
        else:
            MySubView(self._my_sub_model).render(output)

        if self._report_model.args.show_per_day:
            _v1.PerDayView(self._report_model.per_day_model).render(output)
        else:
            _v1.ProjectsView(self._report_model.projects_model).render(output)

        if self._report_model.args.show_details:
            _v1.ActivitiesView(self._report_model.activities_model).render(output)

            _v1.DetailsView(
                self._report_model.details_model, show_comments=self._report_model.args.show_comments
            ).render(output)

        TagSummarySubView(self._my_tag_model, self._my_azdo_wi, self._report_model.args.show_details).render(output)

        #MySubView(self._my_sub_model).render(output)

_v1.register_component(_v1.ReportView, MyReportView)
