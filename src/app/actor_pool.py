# import typing as ty
# from src.app.actor import System
# from src.app.journal import Journal

# @lru_cache(maxsize=1)
# def get_journal(settings: Settings):
#     get_system(settings=settings)
#     journal = Journal(
#         eventstore=get_eventstore(settings),
#         mailbox=MailBox.build(),
#         ref=settings.actor_refs.JOURNAL,
#     )
#     return journal
