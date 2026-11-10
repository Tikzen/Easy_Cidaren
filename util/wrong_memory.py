import json
import os
import threading
import time

from log.log import Log
from util.app_path import config_dir
from util.text_norm import norm_key

MEM_FILE = 'wrong_memory.json'
_lock = threading.Lock()
_memory = None

memory_logger = Log('wrong_memory')


def _mem_path():
    return os.path.join(config_dir(), MEM_FILE)


def _key(mode, content, remark):
    return f"{mode}|{norm_key(content)}|{norm_key(remark)}"


def load_memory(force=False):
    global _memory
    if _memory is None or force:
        path = _mem_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                _memory = data if isinstance(data, dict) else {}
            except Exception as e:
                memory_logger.error(f"加载错题记忆失败: {e}")
                _memory = {}
        else:
            _memory = {}
    return _memory


def lookup(mode, content, remark):
    """按 题型+题干+中文释义 查错题记忆, 返回标准答案内容列表或 None"""
    entry = load_memory().get(_key(mode, content, remark))
    if not isinstance(entry, dict):
        return None
    answers = entry.get('answers')
    if not isinstance(answers, list):
        return None
    answers = [a for a in answers if isinstance(a, str) and a.strip()]
    return answers or None


def record(mode, content, remark, answers):
    """判错后记录服务端返回的标准答案(选项内容/短语), 再次判错覆盖旧值"""
    clean = [a for a in answers if isinstance(a, str) and a.strip()]
    if not clean:
        return
    key = _key(mode, content, remark)
    with _lock:
        memory = load_memory()
        memory[key] = {
            'mode': mode,
            'content': content if isinstance(content, str) else '',
            'remark': remark if isinstance(remark, str) else '',
            'answers': clean,
            'updated': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        try:
            with open(_mem_path(), 'w', encoding='utf-8') as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
            memory_logger.info(f"记录错题答案: mode={mode} answers={clean}")
        except Exception as e:
            memory_logger.error(f"保存错题记忆失败: {e}")