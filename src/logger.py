import logging
import logging.config
import os

def setup_logger(config_path='config/logging.conf'):
    """
    logging.confファイルからロギング設定を読み込み、ロガーをセットアップする。
    """
    # ログファイル用のディレクトリが存在しない場合は作成
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if os.path.exists(config_path):
        logging.config.fileConfig(config_path, disable_existing_loggers=False)
    else:
        # コンフィグファイルがない場合は基本的な設定を行う
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.warning(f"警告: ロギング設定ファイルが見つかりません: {config_path}。基本的な設定でフォールバックします。")

# モジュールインポート時にロガーをセットアップ
setup_logger()

def get_logger(name):
    """
    指定された名前でロガーインスタンスを取得する。
    """
    return logging.getLogger(name)
