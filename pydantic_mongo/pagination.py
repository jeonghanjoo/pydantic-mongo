from .errors import PaginationError
from base64 import b64decode, b64encode
from bson import ObjectId
from pydantic import BaseModel
from pydantic.generics import GenericModel
from typing import Generic, TypeVar, Any
import bson
import zlib

DataT = TypeVar('DataT')


class Edge(GenericModel, Generic[DataT]):
    node: DataT
    cursor: str

    class Config:
        json_encoders = {ObjectId: str}


def encode_pagination_cursor(data: list) -> str:
    byte_data = bson.BSON.encode({'v': data})
    byte_data = zlib.compress(byte_data, 9)
    return b64encode(byte_data).decode('utf-8')


def decode_pagination_cursor(data: str) -> list:
    try:
        byte_data = b64decode(data.encode('utf-8'))
        byte_data = zlib.decompress(byte_data)
        result = bson.BSON(byte_data).decode()
        return result['v']
    except Exception:
        raise PaginationError('Invalid cursor')


def get_pagination_cursor_payload(model: BaseModel, keys: list[str]) -> list[Any]:
    model_dict = model.dict()
    model_dict['_id'] = model_dict['id']

    return [
        __evaluate_dot_notation(model_dict, key) for key in keys
    ]


def __evaluate_dot_notation(data: Any, path: str):
    pieces = path.split('.')

    if len(pieces) == 1:
        return data[path]

    current_data = data

    for piece in pieces:
        if isinstance(current_data, list) or isinstance(current_data, tuple):
            current_data = current_data[int(piece)]
        else:
            current_data = current_data[piece]

    return current_data
