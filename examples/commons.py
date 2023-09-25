from fastapi import Header


def get_version(x_version: str = Header(None)) -> str:
    return x_version