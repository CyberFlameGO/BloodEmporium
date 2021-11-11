from pprint import pprint

class Node:
    # TODO pass in colour, calculate is_accessible, is_user_claimed, is_entity claimed from it
    #  - also dont need is_entity_claimed since they arent really circles
    def __init__(self, node_id, name, value, position, is_accessible, is_user_claimed, is_entity_claimed):
        self.node_id = node_id
        self.name = name
        self.value = value
        self.x, self.y = position
        self.is_accessible = is_accessible
        self.is_user_claimed = is_user_claimed
        self.is_entity_claimed = is_entity_claimed

    @classmethod
    def from_dict(cls, data, **kwargs):
        position = (int(data["x"]), int(data["y"]))
        node = cls(data['node_id'], data['name'], data['value'], position, data['is_accessible'], data['is_user_claimed'], data['is_entity_claimed'])
        for attribute, val in kwargs.items():
            node.__setattr__(attribute, val)
        return node

    def print(self):
        pprint(self.__dict__)

    def get_id(self):
        return self.node_id

    def set_value(self, value):
        self.value = value
        return self

    def set_user_claimed(self, is_claimed):
        self.is_user_claimed = is_claimed

    def get_tuple(self):
        data = {
            "node_id": self.node_id,
            "name": self.name,
            "value": self.value,
            "x": str(self.x),
            "y": str(self.y),
            "is_accessible": self.is_accessible,
            "is_user_claimed": self.is_user_claimed,
            "is_entity_claimed": self.is_entity_claimed,

            # pyvis attributes
            "title": f"{self.value}, " + ("user claimed" if self.is_user_claimed else "entity claimed" if self.is_entity_claimed else "not claimed"),
            "color": "red" if self.is_user_claimed else "yellow" if self.is_accessible else "gray" if not self.is_entity_claimed else "black",
            "physics": False
        }
        return self.node_id, data

    def get_dict(self):
        t = self.get_tuple()
        return {t[0]: t[1]}
