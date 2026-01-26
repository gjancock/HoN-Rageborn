import logging

logger = logging.getLogger("rageborn")

def global_thread_exception_handler(args):
    logger.exception(
        "[THREAD-CRASH] Unhandled exception",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
    )