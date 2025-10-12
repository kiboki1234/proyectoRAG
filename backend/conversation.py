"""
Gestor de conversaciones persistentes.
Permite guardar, cargar y listar conversaciones en formato JSON.
"""
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
from logger import get_logger

logger = get_logger("rag_offline.conversation")


class ConversationManager:
    """Gestiona conversaciones persistentes en disco"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ConversationManager initialized at {storage_dir}")
    
    def save_conversation(self, conv_id: str, messages: List[Dict]) -> None:
        """
        Guarda conversación en JSON.
        
        Args:
            conv_id: ID único de la conversación
            messages: Lista de mensajes con estructura {role, content, citations, ...}
        """
        try:
            file_path = self.storage_dir / f"{conv_id}.json"
            
            # Si existe, actualizar; si no, crear nuevo
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    existing["messages"] = messages
                    existing["updated_at"] = datetime.now().isoformat()
                    data = existing
            else:
                data = {
                    "id": conv_id,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "messages": messages
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved conversation {conv_id} with {len(messages)} messages")
        except Exception as e:
            logger.error(f"Error saving conversation {conv_id}: {e}")
            raise
    
    def load_conversation(self, conv_id: str) -> Optional[Dict]:
        """
        Carga conversación desde JSON.
        
        Args:
            conv_id: ID de la conversación
        
        Returns:
            Dict con {id, created_at, updated_at, messages} o None si no existe
        """
        try:
            file_path = self.storage_dir / f"{conv_id}.json"
            if not file_path.exists():
                logger.warning(f"Conversation {conv_id} not found")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded conversation {conv_id} with {len(data.get('messages', []))} messages")
            return data
        except Exception as e:
            logger.error(f"Error loading conversation {conv_id}: {e}")
            return None
    
    def list_conversations(self, limit: int = 50) -> List[Dict]:
        """
        Lista todas las conversaciones (metadata).
        
        Args:
            limit: Número máximo de conversaciones a retornar
        
        Returns:
            Lista de {id, created_at, updated_at, message_count}
        """
        try:
            conversations = []
            for file in self.storage_dir.glob("*.json"):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        conversations.append({
                            "id": data["id"],
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at"),
                            "message_count": len(data.get("messages", []))
                        })
                except Exception as e:
                    logger.warning(f"Skipping corrupted file {file}: {e}")
                    continue
            
            # Ordenar por fecha de actualización (más recientes primero)
            conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            
            logger.info(f"Listed {len(conversations)} conversations")
            return conversations[:limit]
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []
    
    def delete_conversation(self, conv_id: str) -> bool:
        """
        Elimina una conversación.
        
        Args:
            conv_id: ID de la conversación
        
        Returns:
            True si se eliminó, False si no existía
        """
        try:
            file_path = self.storage_dir / f"{conv_id}.json"
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted conversation {conv_id}")
                return True
            else:
                logger.warning(f"Conversation {conv_id} not found for deletion")
                return False
        except Exception as e:
            logger.error(f"Error deleting conversation {conv_id}: {e}")
            return False
