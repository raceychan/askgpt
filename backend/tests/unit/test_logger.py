from askgpt.domain._log import debug_sink, prod_sink, update_sink


def test_logger():
    update_sink(prod_sink)
    update_sink(debug_sink)
