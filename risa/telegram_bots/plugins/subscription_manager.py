from typing import Dict, List

from risa.common.subscriptions import Subscriptions


class SubscriptionManager:
    @staticmethod
    def add_subscription(url: str, chat_ids: List[int], app: str) -> Dict:
        subs = Subscriptions(app=app)
        sub = subs.add_subscription(url=url, chat_ids=chat_ids)
        subs.save()
        return sub

    @staticmethod
    def get_subscriptions_as_text(app: str) -> str:
        subs = Subscriptions(app).get_subscriptions()
        text = "Subscriptions:\n"
        tab = "\t\t"

        for url_key, subscription in subs.items():
            text += f"{tab}{url_key}:\n"

            for k, v in subscription.items():
                text += f"{tab}{tab}{k}: {v}\n"
            text += f"{tab}{tab}{tab}/r_{url_key}\n\n"
        return text

    @staticmethod
    def remove_subscription(app: str, url_key: str):
        subs = Subscriptions(app)
        subs.remove(key_to_remove=url_key)
        subs.save()
