from datetime import datetime


class Entry:
    def __init__(
        self,
        entry_datetime: datetime,
        name: str,
        is_current_entry: bool,
        comment: str = None,
        tags: list = None,
    ):
        self.datetime = entry_datetime
        self.name = name
        self.is_current_entry = is_current_entry
        self.comment = comment
        self.tags = tags

    def __str__(self):
        str_components = [self.datetime.strftime("%Y-%m-%d %H:%M%z"), self.name]

        if self.comment or self.tags:
            str_components.append(" # ")

        if self.comment:
            str_components.append(self.comment)

        if self.tags:
            tag_str = " ".join([ f"@{t[0]}:{t[1]}" for t in self.tags ])
            str_components.append(tag_str)

        return " ".join(str_components)
