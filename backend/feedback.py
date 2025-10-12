"""
Sistema de feedback de usuarios.
Permite registrar y analizar la satisfacción con las respuestas del sistema.
"""
from pathlib import Path
from typing import Literal, Dict
from datetime import datetime
import json
from logger import get_logger

logger = get_logger("rag_offline.feedback")

FeedbackType = Literal['positive', 'negative']


class FeedbackManager:
    """Gestiona feedback de usuarios sobre respuestas"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"FeedbackManager initialized at {storage_path}")
    
    def save_feedback(
        self, 
        message_id: str, 
        feedback: FeedbackType, 
        question: str = None,
        answer: str = None,
        metadata: dict = None
    ) -> None:
        """
        Guarda feedback en formato JSONL.
        
        Args:
            message_id: ID del mensaje evaluado
            feedback: 'positive' o 'negative'
            question: Pregunta original (opcional)
            answer: Respuesta dada (opcional)
            metadata: Metadata adicional (cached, temperature, etc.)
        """
        try:
            entry = {
                "message_id": message_id,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": answer[:200] if answer else None,  # Solo primeros 200 chars
                "metadata": metadata or {}
            }
            
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            logger.info(f"Saved {feedback} feedback for message {message_id}")
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """
        Calcula estadísticas de feedback.
        
        Returns:
            Dict con total, positive, negative, satisfaction_rate
        """
        if not self.storage_path.exists():
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "satisfaction_rate": 0.0
            }
        
        total = positive = negative = 0
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        total += 1
                        if data["feedback"] == "positive":
                            positive += 1
                        else:
                            negative += 1
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping corrupted feedback line: {e}")
                        continue
            
            satisfaction_rate = (positive / total) if total > 0 else 0.0
            
            logger.info(f"Feedback stats: {positive}/{total} positive ({satisfaction_rate:.1%})")
            
            return {
                "total": total,
                "positive": positive,
                "negative": negative,
                "satisfaction_rate": satisfaction_rate
            }
        except Exception as e:
            logger.error(f"Error calculating feedback stats: {e}")
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "satisfaction_rate": 0.0
            }
    
    def get_recent_feedback(self, limit: int = 100) -> list:
        """
        Obtiene los últimos N feedback.
        
        Args:
            limit: Número máximo de feedback a retornar
        
        Returns:
            Lista de feedback (más recientes primero)
        """
        if not self.storage_path.exists():
            return []
        
        feedback_list = []
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        feedback_list.append(data)
                    except json.JSONDecodeError:
                        continue
            
            # Retornar los últimos N (más recientes primero)
            return list(reversed(feedback_list[-limit:]))
        except Exception as e:
            logger.error(f"Error getting recent feedback: {e}")
            return []
