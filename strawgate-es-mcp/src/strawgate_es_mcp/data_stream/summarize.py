import re
from typing import TYPE_CHECKING, Any

from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel, Field, RootModel

if TYPE_CHECKING:
    from elastic_transport import ObjectApiResponse


class DataStreamFieldSummary(BaseModel):
    field: str = Field(description="The name of the field")
    type: str = Field(description="The type of the field")
    sample_values: list[str | bool | int | float | None] | None = Field(
        description="A small set of values of the field from documents in the data stream"
    )


class DataStreamRowExample(RootModel[dict[str, Any]]):
    pass


class DataStreamSummary(BaseModel):
    data_stream: str = Field(description="The name of the data stream")
    fields: list[DataStreamFieldSummary] = Field(description="The fields of the data stream")
    sample_rows: list[DataStreamRowExample] = Field(description="A small set of rows from the data stream")


async def summarize_data_stream(es: AsyncElasticsearch, data_stream: str) -> DataStreamSummary:
    """
    Summarize the data stream.
    """

    # make sure the data stream only contains alphanumeric -, _, . and *
    if not re.match(r"^[a-zA-Z0-9\-_\.\*]+$", data_stream):
        msg = f"Invalid data stream name: {data_stream}"
        raise ValueError(msg)

    esql_query = f"FROM {data_stream} | LIMIT 200"
    result: ObjectApiResponse[dict[str, Any]] = await es.esql.query(query=esql_query, columnar=True)

    columns: list[dict[str, Any]] | None = result.body.get("columns")

    if not columns:
        return DataStreamSummary(data_stream=data_stream, fields=[], sample_rows=[])

    values: list[list[str | bool | int | float | None]] | None = result.body.get("values")

    if not values:
        return DataStreamSummary(data_stream=data_stream, fields=[], sample_rows=[])

    field_summaries: list[DataStreamFieldSummary] = []

    for i, column in enumerate(columns):
        field_name: str | None = column.get("name")
        field_type: str | None = column.get("type")

        if not field_name or not field_type:
            continue

        column_values: list[str | bool | int | float | None] | None = values[i]

        if not column_values:
            continue

        unique_values: set[Any] = set()

        for value in column_values:
            if value is None:
                continue

            unique_values.add(value)

        if not unique_values:
            continue

        field_summaries.append(DataStreamFieldSummary(field=field_name, type=field_type, sample_values=list(unique_values)[:10]))

    row_examples: list[DataStreamRowExample] = []

    for example_row_number in range(5):
        row_example: dict[str, Any] = {}

        for column_index, column_info in enumerate(columns):
            column_values: list[str | bool | int | float | None] | None = values[column_index]

            if example_row_number >= len(column_values):
                break

            value: str | bool | int | float | None = column_values[example_row_number]
            if value is None:
                continue

            row_example[column_info["name"]] = value

        row_examples.append(DataStreamRowExample(root=row_example))

    return DataStreamSummary(data_stream=data_stream, fields=field_summaries, sample_rows=row_examples)


async def summarize_data_streams(es: AsyncElasticsearch, data_streams: list[str]) -> list[DataStreamSummary]:
    return [await summarize_data_stream(es, data_stream) for data_stream in data_streams]
