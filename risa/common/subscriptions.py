from typing import Any, Dict, List, Optional, Union

import re

from risa.common.constants import SUBSCRIPTIONS_FILE
from risa.common.utils import Utils


class ImportExportSubscriptionFile:
    @staticmethod
    def import_subscription_yaml() -> Dict:
        return Utils().import_yaml(file_path=SUBSCRIPTIONS_FILE) or {}

    @staticmethod
    def export_subscription_yaml(data) -> None:
        Utils().export_yaml(file_path=SUBSCRIPTIONS_FILE, data=data)


class Subscriptions(ImportExportSubscriptionFile):
    def __init__(self, app: str) -> None:
        self._subscriptions = self.import_subscription_yaml()
        self._app = app
        if self._app:
            self._subscriptions[app] = self._subscriptions.get(app, {})

    @property
    def subscriptions(self) -> Dict[str, Any]:
        return self._subscriptions

    def list(self) -> Union[List, Dict]:
        return self._subscriptions

    def save(self) -> bool:
        self.export_subscription_yaml(data=self._subscriptions)
        return True

    def get_subscriptions(self) -> Dict:
        return self._subscriptions.get(self._app)

    def add_subscription(self, url: str, **kwargs) -> Dict:
        app = self._subscriptions.get(self._app, {})
        url_key = self._get_url_key(url=url)

        app[url_key] = app.get(url_key, {})
        app[url_key]["url_key"] = url_key
        app[url_key]["url"] = url

        for k, v in kwargs.items():
            existing_value = app[url_key].get(k)
            if isinstance(existing_value, list):
                if v not in existing_value:
                    existing_value.extend(v)
                    app[url_key][k] = existing_value
            elif isinstance(existing_value, dict):
                existing_value.update(v)
                app[url_key][k] = existing_value
            else:
                app[url_key][k] = v
        return app[url_key]

    def remove(self, key_to_remove: str) -> bool:
        self._subscriptions[self._app].pop(key_to_remove)
        return True

    def update_checkpoint(self, url_key: str, checkpoint: str) -> bool:
        self._subscriptions[self._app][url_key]["checkpoint"] = checkpoint
        return True

    @staticmethod
    def _get_url_key(url: str) -> str:
        url_cut = re.search(r"\w+\.\w+/.+", url)
        url_cut = url_cut.group()
        return re.sub(r'[-+!~@#$%^&*()={}\[\]:;<.>?/\'"]', "", url_cut)
