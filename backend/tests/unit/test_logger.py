from src.domain._log import logger, prod_sink, update_sink


def test_logger():
    logger.error("dev")
    update_sink(prod_sink)
    logger.info("prod")
