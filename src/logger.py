import logging
import logging.config
import os

def setup_logging(config_path='config/logging.conf'):
    """
    ロギングを設定する関数。

    Args:
        config_path (str): ロギング設定ファイルのパス。
    """
    if os.path.exists(config_path):
        logging.config.fileConfig(config_path, disable_existing_loggers=False)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.warning(f"設定ファイルが見つかりません: {config_path}. 基本設定でロガーを初期化しました。")

def get_logger(name):
    """
    ロガーを取得する関数。

    Args:
        name (str): ロガーの名前。

    Returns:
        logging.Logger: ロガーオブジェクト。
    """
    return logging.getLogger(name)
