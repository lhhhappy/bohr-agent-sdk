import inspect
from collections.abc import Sequence
from typing import Annotated, Any, List, Optional

import jsonpickle
from mcp.server.fastmcp.exceptions import InvalidSignature
from mcp.server.fastmcp.utilities.func_metadata import (
    ArgModelBase,
    _get_typed_annotation,
    FuncMetadata,
)
from mcp.server.fastmcp.utilities.types import Image
from mcp.types import (
    EmbeddedResource,
    ImageContent,
    TextContent,
)
from pydantic import Field, WithJsonSchema, create_model
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


def get_metadata(
    func_name: str,
    parameters: List[inspect.Parameter],
    skip_names: Sequence[str] = (),
    globalns: dict = {},
) -> FuncMetadata:
    dynamic_pydantic_model_params: dict[str, Any] = {}
    for param in parameters:
        if param.name.startswith("_"):
            raise InvalidSignature(
                f"Parameter {param.name} of {func_name} cannot start with '_'"
            )
        if param.name in skip_names:
            continue
        annotation = param.annotation

        # `x: None` / `x: None = None`
        if annotation is None:
            annotation = Annotated[
                None,
                Field(
                    default=param.default
                    if param.default is not inspect.Parameter.empty
                    else PydanticUndefined
                ),
            ]

        # Untyped field
        if annotation is inspect.Parameter.empty:
            annotation = Annotated[
                Any,
                Field(),
                # 🤷
                WithJsonSchema({"title": param.name, "type": "string"}),
            ]

        field_info = FieldInfo.from_annotated_attribute(
            _get_typed_annotation(annotation, globalns),
            param.default
            if param.default is not inspect.Parameter.empty
            else PydanticUndefined,
        )
        dynamic_pydantic_model_params[param.name] = (
            field_info.annotation, field_info)
        continue

    arguments_model = create_model(
        f"{func_name}Arguments",
        **dynamic_pydantic_model_params,
        __base__=ArgModelBase,
    )
    resp = FuncMetadata(arg_model=arguments_model)
    return resp


def convert_to_content(
    result: Any,
    job_info: Optional[dict] = None,
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Convert a result to a sequence of content objects."""
    other_contents = []
    if isinstance(result, Image):
        other_contents.append(result.to_image_content())
        result = None

    if isinstance(result, TextContent | ImageContent | EmbeddedResource):
        other_contents.append(result)
        result = None

    if isinstance(result, list | tuple):
        for item in result.copy():
            if isinstance(item, Image):
                other_contents.append(item.to_image_content())
                result.remove(item)
            elif isinstance(
                    result, TextContent | ImageContent | EmbeddedResource):
                other_contents.append(item)
                result.remove(item)

    if isinstance(result, dict):
        for key, value in list(result.items()):
            if isinstance(value, Image):
                other_contents.append(value.to_image_content())
                del result[key]
            elif isinstance(
                    value, TextContent | ImageContent | EmbeddedResource):
                other_contents.append(value)
                del result[key]

    if not isinstance(result, str):
        result = jsonpickle.dumps(result)

    return [TextContent(type="text", text=result, job_info=job_info)] \
        + other_contents
