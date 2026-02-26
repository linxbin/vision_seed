import json
import os
from datetime import datetime
from typing import List, Dict, Any


class DataManager:
    """数据管理器 - 负责训练记录的持久化存储和读取"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.project_root, "data")
        self.records_file = os.path.join(self.data_dir, "records.json")
        
        # 确保data目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化记录文件（如果不存在）
        if not os.path.exists(self.records_file):
            self._init_records_file()
    
    def _init_records_file(self):
        """初始化记录文件"""
        initial_data = {
            "sessions": []
        }
        self._write_json(initial_data)
    
    def _read_json(self) -> Dict[str, Any]:
        """安全读取JSON文件"""
        try:
            if os.path.exists(self.records_file):
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"sessions": []}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading records file: {e}")
            # 返回默认数据并尝试修复文件
            self._init_records_file()
            return {"sessions": []}
    
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
            
            # 添加会话ID（基于时间戳）
            if 'session_id' not in session_data:
                session_data['session_id'] = session_data['timestamp'].replace(':', '').replace('-', '').replace('T', '-')
            
            # 计算正确率
            if 'accuracy_rate' not in session_data:
                total = session_data['total_questions']
                correct = session_data['correct_count']
                session_data['accuracy_rate'] = round((correct / total) * 100, 1) if total > 0 else 0.0
            
            # 获取现有数据
            data = self._read_json()
            
            # 添加新会话到列表开头（最新在前）
            data['sessions'].insert(0, session_data)
            
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