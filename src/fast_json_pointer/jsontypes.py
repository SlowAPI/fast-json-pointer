JsonObj = dict[str, "JsonType"]
JsonArr = list["JsonType"]
JsonType = JsonObj | JsonArr | str | bool | int | float | None
