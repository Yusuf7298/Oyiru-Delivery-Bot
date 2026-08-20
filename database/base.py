from typing import Dict, Any

class Base:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        data = {}
        for k, v in self.__dict__.items():
            if k.startswith("_") and k != "_id":
                continue
            data[k] = v
        return data

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_"))
        return f"<{self.__class__.__name__}({attrs})>"