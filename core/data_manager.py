import json
import os
import shutil
from typing import List, Dict, Any, Tuple
from config import E_SIZE_LEVELS
from core.app_paths import get_install_root, get_user_data_dir


class DataManager:
    """数据管理器 - 负责训练记录的持久化存储和读取"""
    CURRENT_SCHEMA_VERSION = 2
    
    def __init__(self):
        self.data_dir = get_user_data_dir()
        self.records_file = os.path.join(self.data_dir, "records.json")

        # 初始化记录文件（如果不存在）
        if not os.path.exists(self.records_file):
            self._migrate_or_init_records()

    def _migrate_or_init_records(self):
        install_root = get_install_root()
        legacy_records = os.path.join(install_root, "data", "records.json")
        if os.path.exists(legacy_records):
            try:
                os.makedirs(self.data_dir, exist_ok=True)
                shutil.copyfile(legacy_records, self.records_file)
                return
            except OSError as e:
                print(f"Error migrating legacy records file: {e}")
        self._init_records_file()
    
    def _init_records_file(self):
        """初始化记录文件"""
        initial_data = {
            "schema_version": self.CURRENT_SCHEMA_VERSION,
            "sessions": []
        }
        self._write_json(initial_data)

    def _safe_int(self, value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _build_session_id(self, timestamp: str) -> str:
        if not isinstance(timestamp, str) or not timestamp:
            return "unknown-session"
        return timestamp.replace(":", "").replace("-", "").replace("T", "-")

    def _derive_e_size(self, difficulty_level: int) -> int:
        if 1 <= difficulty_level <= len(E_SIZE_LEVELS):
            return E_SIZE_LEVELS[difficulty_level - 1]
        return E_SIZE_LEVELS[0]

    def _normalize_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = session.get("timestamp", "")
        difficulty_level = self._safe_int(session.get("difficulty_level"), 1)
        difficulty_level = max(1, min(len(E_SIZE_LEVELS), difficulty_level))

        total_questions = self._safe_int(session.get("total_questions"), 0)
        total_questions = max(0, total_questions)
        correct_count = self._safe_int(session.get("correct_count"), 0)
        correct_count = max(0, min(total_questions, correct_count))

        wrong_default = max(0, total_questions - correct_count)
        wrong_count = self._safe_int(session.get("wrong_count"), wrong_default)
        wrong_count = max(0, wrong_count)

        duration_seconds = self._safe_float(session.get("duration_seconds"), 0.0)
        duration_seconds = max(0.0, duration_seconds)

        e_size_px = self._safe_int(session.get("e_size_px"), 0)
        if e_size_px <= 0:
            e_size_px = self._derive_e_size(difficulty_level)

        accuracy_rate = session.get("accuracy_rate")
        if accuracy_rate is None:
            accuracy_rate = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0
        else:
            accuracy_rate = self._safe_float(accuracy_rate, 0.0)
        accuracy_rate = max(0.0, min(100.0, accuracy_rate))

        session_id = session.get("session_id")
        if not session_id:
            session_id = self._build_session_id(timestamp)

        return {
            "schema_version": self.CURRENT_SCHEMA_VERSION,
            "timestamp": timestamp,
            "session_id": session_id,
            "difficulty_level": difficulty_level,
            "e_size_px": e_size_px,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "duration_seconds": duration_seconds,
            "accuracy_rate": accuracy_rate,
        }

    def _migrate_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        sessions = data.get("sessions", [])
        if not isinstance(sessions, list):
            sessions = []

        normalized_sessions = []
        changed = False
        for raw_session in sessions:
            if not isinstance(raw_session, dict):
                changed = True
                continue
            normalized = self._normalize_session(raw_session)
            normalized_sessions.append(normalized)
            if normalized != raw_session:
                changed = True

        migrated = {
            "schema_version": self.CURRENT_SCHEMA_VERSION,
            "sessions": normalized_sessions
        }

        if data.get("schema_version") != self.CURRENT_SCHEMA_VERSION:
            changed = True
        if data.get("sessions") != normalized_sessions:
            changed = True

        return migrated, changed
    
    def _read_json(self) -> Dict[str, Any]:
        """安全读取JSON文件"""
        try:
            if os.path.exists(self.records_file):
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                if not isinstance(raw_data, dict):
                    raw_data = {"sessions": []}
                migrated_data, changed = self._migrate_data(raw_data)
                if changed:
                    self._write_json(migrated_data)
                return migrated_data
            else:
                return {"schema_version": self.CURRENT_SCHEMA_VERSION, "sessions": []}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading records file: {e}")
            # 返回默认数据并尝试修复文件
            self._init_records_file()
            return {"schema_version": self.CURRENT_SCHEMA_VERSION, "sessions": []}
    
    def _write_json(self, data: Dict[str, Any]):
        """安全写入JSON文件"""
        try:
            with open(self.records_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error writing records file: {e}")
    
    def save_training_session(self, session_data: Dict[str, Any]) -> bool:
        """
        保存训练会话记录
        
        Args:
            session_data (dict): 训练会话数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 验证必需字段
            required_fields = ['timestamp', 'difficulty_level', 'total_questions', 
                             'correct_count', 'wrong_count', 'duration_seconds']
            for field in required_fields:
                if field not in session_data:
                    raise ValueError(f"Missing required field: {field}")

            normalized_session = self._normalize_session(session_data)

            # 获取现有数据
            data = self._read_json()
            
            # 添加新会话到列表开头（最新在前）
            data['sessions'].insert(0, normalized_session)
            data['schema_version'] = self.CURRENT_SCHEMA_VERSION
            
            # 写回文件
            self._write_json(data)
            
            return True
            
        except Exception as e:
            print(f"Error saving training session: {e}")
            return False
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """获取所有训练会话记录"""
        data = self._read_json()
        return data.get('sessions', [])
    
    def get_latest_session(self) -> Dict[str, Any]:
        """获取最新的训练会话记录"""
        sessions = self.get_all_sessions()
        return sessions[0] if sessions else {}
    
    def get_session_count(self) -> int:
        """获取训练会话总数"""
        return len(self.get_all_sessions())
    
    def clear_all_records(self):
        """清空所有训练记录（谨慎使用）"""
        self._init_records_file()
