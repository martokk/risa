import multiprocessing

from risa.config.config import RISA_BOARDS_BOT_TOKEN, RISA_FEEDS_BOT_TOKEN
from risa.telegram_bots.risa_boards_bot import RisaBoardsBot
from risa.telegram_bots.risa_feeds_bot import RisaFeedsBot


def run_all_telegram_bots() -> None:
    # RisaFeedsBot(token=RISA_FEEDS_BOT_TOKEN)
    # RisaBoardsBot(token=RISA_BOARDS_BOT_TOKEN)

    # creating processes
    p1 = multiprocessing.Process(target=RisaFeedsBot, args=(RISA_FEEDS_BOT_TOKEN,))
    p2 = multiprocessing.Process(target=RisaBoardsBot, args=(RISA_BOARDS_BOT_TOKEN,))

    # starting processes
    p1.start()
    p2.start()

    # wait until processes are finished
    p1.join()
    p2.join()


if __name__ == "__main__":
    run_all_telegram_bots()
