from importlib.resources import files


DISPLAY_ROW_LIMIT = 50

SQL_BLOCK = (
    files("order_generator.extract")
    .joinpath("query.sql")
    .read_text(encoding="utf-8")
    .strip()
    .removesuffix(";")
)
