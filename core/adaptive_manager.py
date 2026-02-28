from typing import Any, Dict, List


class AdaptiveManager:
    """自适应难度 V1：基于最近3次训练的正确率与单题用时进行升降级。"""

    REQUIRED_SESSIONS = 3
    UPGRADE_ACC_THRESHOLD = 85.0
    UPGRADE_SEC_THRESHOLD = 2.2
    DOWNGRADE_ACC_THRESHOLD = 65.0
    DOWNGRADE_SEC_THRESHOLD = 3.8
    COOLDOWN_SESSIONS = 2

    @staticmethod
    def _session_accuracy(session: Dict[str, Any]) -> float:
        if "accuracy_rate" in session:
            try:
                return float(session.get("accuracy_rate", 0.0))
            except (TypeError, ValueError):
                return 0.0
        total = int(session.get("total_questions", 0) or 0)
        correct = int(session.get("correct_count", 0) or 0)
        return round((correct / total) * 100, 1) if total > 0 else 0.0

    @staticmethod
    def _session_avg_seconds(session: Dict[str, Any]) -> float:
        try:
            total = int(session.get("total_questions", 0) or 0)
            duration = float(session.get("duration_seconds", 0.0) or 0.0)
        except (TypeError, ValueError):
            return 0.0
        if total <= 0:
            return 0.0
        return max(0.0, duration / total)

    def evaluate(
        self,
        sessions: List[Dict[str, Any]],
        current_level: int,
        min_level: int,
        max_level: int,
        enabled: bool,
        cooldown_left: int,
    ) -> Dict[str, Any]:
        result = {
            "enabled": enabled,
            "changed": False,
            "old_level": current_level,
            "new_level": current_level,
            "reason_code": "DISABLED",
            "cooldown_left": max(0, int(cooldown_left or 0)),
            "avg_accuracy": None,
            "avg_seconds": None,
        }

        if not enabled:
            return result

        if result["cooldown_left"] > 0:
            result["reason_code"] = "COOLDOWN"
            result["cooldown_left"] -= 1
            return result

        valid = []
        for session in sessions:
            try:
                total = int(session.get("total_questions", 0) or 0)
            except (TypeError, ValueError):
                total = 0
            if total > 0:
                valid.append(session)
            if len(valid) >= self.REQUIRED_SESSIONS:
                break

        if len(valid) < self.REQUIRED_SESSIONS:
            result["reason_code"] = "INSUFFICIENT"
            return result

        acc_values = [self._session_accuracy(s) for s in valid]
        sec_values = [self._session_avg_seconds(s) for s in valid]
        avg_acc = sum(acc_values) / len(acc_values)
        avg_sec = sum(sec_values) / len(sec_values)
        result["avg_accuracy"] = round(avg_acc, 1)
        result["avg_seconds"] = round(avg_sec, 2)

        new_level = current_level
        reason_code = "KEEP"

        if avg_acc >= self.UPGRADE_ACC_THRESHOLD and avg_sec <= self.UPGRADE_SEC_THRESHOLD:
            new_level = max(min_level, current_level - 1)
            reason_code = "UP"
        elif avg_acc < self.DOWNGRADE_ACC_THRESHOLD or avg_sec >= self.DOWNGRADE_SEC_THRESHOLD:
            new_level = min(max_level, current_level + 1)
            reason_code = "DOWN"

        result["reason_code"] = reason_code
        result["new_level"] = new_level
        result["changed"] = new_level != current_level
        result["cooldown_left"] = self.COOLDOWN_SESSIONS if result["changed"] else 0
        return result
