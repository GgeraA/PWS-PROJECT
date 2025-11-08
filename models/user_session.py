import psycopg2
from config import Config
from datetime import datetime, timedelta, timezone
import json
from utils.audit_helper import log_event

class UserSession:
    def __init__(self, id=None, user_id=None, session_token=None, created_at=None, 
                 expires_at=None, is_active=True, ip_address=None, user_agent=None,
                 location_data=None, last_activity=None):
        self.id = id
        self.user_id = user_id
        self.session_token = session_token
        self.created_at = created_at
        self.expires_at = expires_at
        self.is_active = is_active
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.location_data = location_data
        self.last_activity = last_activity

    def save(self):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_sessions 
            (user_id, session_token, created_at, expires_at, is_active, ip_address, user_agent, location_data, last_activity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (self.user_id, self.session_token, self.created_at, self.expires_at, 
              self.is_active, self.ip_address, self.user_agent, self.location_data, self.last_activity))
        self.id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return self.id

    def update(self):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_sessions 
            SET is_active=%s, last_activity=%s
            WHERE id=%s
        """, (self.is_active, self.last_activity, self.id))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def find_by_token(session_token):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, session_token, created_at, expires_at, 
                   is_active, ip_address, user_agent, location_data, last_activity
            FROM user_sessions 
            WHERE session_token=%s AND is_active=true AND expires_at > NOW()
        """, (session_token,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return UserSession(*row)
        return None

    @staticmethod
    def find_active_by_user(user_id):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, session_token, created_at, expires_at, 
                   is_active, ip_address, user_agent, location_data, last_activity
            FROM user_sessions 
            WHERE user_id=%s AND is_active=true AND expires_at > NOW()
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [UserSession(*row) for row in rows]

    @staticmethod
    def invalidate_session(session_token):
        log_event("Logout attempt", session_token)
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_sessions 
            SET is_active=false 
            WHERE session_token=%s AND is_active=true
            RETURNING id
        """, (session_token,))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return bool(row)

    @staticmethod
    def invalidate_all_user_sessions(user_id):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_sessions 
            SET is_active=false 
            WHERE user_id=%s AND is_active=true
        """, (user_id,))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def cleanup_expired():
        """Marcar como inactivas las sesiones expiradas"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_sessions 
            SET is_active=false 
            WHERE expires_at <= NOW() AND is_active=true
        """)
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def refresh_session(session_token, extension_hours=24):
        """Renovar una sesión extendiendo su tiempo de expiración"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        new_expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=extension_hours)
        cur.execute("""
            UPDATE user_sessions 
            SET expires_at=%s, last_activity=NOW()
            WHERE session_token=%s AND is_active=true
            RETURNING id
        """, (new_expires_at, session_token))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return bool(row)

    @staticmethod
    def update_last_activity(session_token):
        """Actualizar la última actividad de una sesión"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_sessions 
            SET last_activity=NOW()
            WHERE session_token=%s AND is_active=true
        """, (session_token,))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def get_session_info(session_token):
        """Obtener información detallada de una sesión"""
        session = UserSession.find_by_token(session_token)
        if not session:
            return None
        
        # Parsear location_data si existe
        location_info = {}
        if session.location_data:
            try:
                location_info = json.loads(session.location_data)
            except:
                location_info = {"error": "Could not parse location data"}
                raise
        
        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "location": location_info,
            "is_active": session.is_active
        }