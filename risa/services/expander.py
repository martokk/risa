from typing import Union, List


class Expander:
    def __init__(self, service: str) -> None:
        self.service = service
        self.service_masks = {
            'twitter': 'https://www.twitter.com/{data}',
            'chaturbate': 'https://www.chaturbate.com/{data}',
            'manyvids': 'https://{data}.manyvids.com/',
        }

    def expand(self, obj: Union[str, List]) -> Union[str, List]:
        if service_mask := self.service_masks.get(self.service):
            if isinstance(obj, List):
                return [itm.lower() if 'http' in itm else service_mask.replace("{data}", itm.lower()) for itm in obj]
            else:
                return obj.lower() if 'http' in obj else service_mask.replace("{data}", obj.lower())
