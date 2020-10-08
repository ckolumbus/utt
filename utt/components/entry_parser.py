import re
from typing import Optional

from dateutil.parser import parse

from ..data_structures.entry import Entry
from .local_timezone import LocalTimezone

DATE_REGEX = r"(?P<date>\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{1,2})"
TIMEZONE_REGEX = r"(?P<timezone>[+-]{1}\d{2}:{0,1}\d{2})"
NAME_REGEX = r"\s+(?P<name>[^\s].*?)"
COMMENT_REGEX = r"\s{2}#\s(?P<comment>.*$)?"
COMMENT_TAGS_REGEX = r"(^|\s)#(?P<tag>.*?):(?P<value>.*?)(?=\s|$)"

WITH_TZ = re.compile("".join([DATE_REGEX, TIMEZONE_REGEX, NAME_REGEX, r"($|", COMMENT_REGEX, ")"]))

WITHOUT_TZ = re.compile("".join([DATE_REGEX, NAME_REGEX, r"($|", COMMENT_REGEX, ")"]))

TAGS = re.compile(COMMENT_TAGS_REGEX)


class EntryParser:
    def __init__(self, local_timezone: LocalTimezone):
        self._local_timezone = local_timezone

    def parse(self, string: str) -> Optional[Entry]:
        match_wo_tz = WITHOUT_TZ.match(string)
        match_w_tz = WITH_TZ.match(string)
        match = match_w_tz if match_w_tz is not None else match_wo_tz

        if match is None:
            return None

        groupdict = match.groupdict()

        if "date" not in groupdict or "name" not in groupdict:
            return None

        date_str = groupdict["date"]
        if "timezone" in groupdict:
            date_str += groupdict["timezone"].replace(":", "")
            date = parse(date_str)
        else:
            date = parse(date_str)
            date = self._local_timezone.localize(date)

        name = groupdict["name"]
        comment = groupdict.get("comment")

        if comment:
            match_tags = TAGS.findall(comment)
            tags = [(t, v) for s, t, v in match_tags]
            comment = TAGS.sub("", comment).strip()

            # if comment is empty after tags are removed
            if not comment.strip():
                comment = None
        else:
            tags = None

        return Entry(date, name, False, comment=comment, tags=tags)
