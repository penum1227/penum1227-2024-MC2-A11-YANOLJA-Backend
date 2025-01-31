# app/utils/logger.py

import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    지정된 이름과 로그 파일로 로거를 설정하고 반환합니다.
    로그 파일의 디렉토리가 없으면 생성합니다.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 기존 핸들러 제거
    if logger.hasHandlers():
        logger.handlers.clear()

    # 로그 파일 경로의 디렉토리 생성
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # RotatingFileHandler 설정
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
