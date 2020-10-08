import datetime
import itertools
from collections import defaultdict
from typing import Dict, List

from utt.api import _v1
from utt.report.azdo.wi import AzdoWiQuery

from ..components.output import Output
from ..data_structures.activity import Activity
from ..report import formatter
from ..report.common import filter_activities_by_type, print_dicts


class TagSummaryModel:
    def __init__(self, activities: List[Activity]):
        self._activities = activities
        self.tags = groupby_tag(filter_activities_by_type(activities, Activity.Type.WORK))


def groupby_tag(activities: List[Activity]) -> List[Dict]:

    result = defaultdict(lambda: {"key": "", "value": "", "duration": datetime.timedelta(0)})

    for act in activities:
        if act.tags:
            for tag in act.tags:
                key = f"{tag[0]}:{tag[1]}"
                result[key]["duration"] += act.duration
                result[key]["tag"] = tag[0]
                result[key]["value"] = tag[1]

    return dict(result)


_v1.register_component(TagSummaryModel, TagSummaryModel)


class TagSummarySubView:
    def __init__(self, model: TagSummaryModel, azdo: AzdoWiQuery):
        self._model = model
        self._azdo = azdo

    def print_tags(self, dcts: Dict[str, Dict], output: Output) -> None:
        format_string = "({duration}) {tag:<{tag_max_length}}: {value} {wi}"

        tag_max_length = max(itertools.chain([0], (len(dcts[key]["tag"]) for key in dcts)))
        for key in dict(sorted(dcts.items(), key=lambda item: item[0])):
            dct = dcts[key]
            context = {"tag_max_length": tag_max_length}

            context["wi"] = ""
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
    def __init__(self, activities: _v1.Activities):
        self._activities = activities

    @property
    def activity_count(self):
        return len(self._activities)


_v1.register_component(MySubModel, MySubModel)


class MySubView:
    def __init__(self, my_sub_model: MySubModel):
        self._my_sub_model = my_sub_model

    def render(self, output: _v1.Output) -> None:
        print(f"Number of activities: {self._my_sub_model.activity_count}", file=output)


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
        _v1.SummaryView(self._report_model.summary_model).render(output)

        if self._report_model.args.show_per_day:
            _v1.PerDayView(self._report_model.per_day_model).render(output)
        else:
            _v1.ProjectsView(self._report_model.projects_model).render(output)

        _v1.ActivitiesView(self._report_model.activities_model).render(output)

        if (
            self._report_model.args.range.start == self._report_model.args.range.end
        ) or self._report_model.args.show_details:
            _v1.DetailsView(
                self._report_model.details_model, show_comments=self._report_model.args.show_comments
            ).render(output)

        MySubView(self._my_sub_model).render(output)

        TagSummarySubView(self._my_tag_model, self._my_azdo_wi).render(output)


_v1.register_component(_v1.ReportView, MyReportView)
