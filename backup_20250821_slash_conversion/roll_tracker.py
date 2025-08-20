import sqlite3
from datetime import datetime
import json
import os
from typing import List, Dict, Any, Optional

class RollTracker:
    def __init__(self, db_path: str = None):
        """
        Initierar RollTracker med en specifik databassökväg.
        Skapar databasen och nödvändiga tabeller om de inte redan finns.
        """
        if db_path is None:
            # Använd en absolut sökväg baserad på skriptets placering
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(script_dir), 'data')
            # Skapa data-mappen om den inte finns
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, 'rolls.db')
        else:
            self.db_path = db_path
            
        self.current_session = None
        print(f"Använder databasfil: {self.db_path}")
        self.setup_database()
    
    def setup_database(self):
        """
        Skapar databasen och de nödvändiga tabellerna om de inte redan finns.
        Vi använder två tabeller:
        - sessions: För att spåra spelsessioner
        - rolls: För att spara alla tärningskast
        """
        with sqlite3.connect(self.db_path) as conn:
            # Skapar en tabell för spelsessioner
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    description TEXT
                )
            """)
            
            # Skapar en tabell för tärningskast
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rolls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    session_id TEXT,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    command_type TEXT NOT NULL,
                    num_dice INTEGER NOT NULL,
                    sides INTEGER NOT NULL,
                    modifier INTEGER DEFAULT 0,
                    target INTEGER,
                    success INTEGER,
                    roll_values TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Kontrollera om kolumnerna för perfekt/fummel finns, lägg till dem om de saknas
            try:
                cursor = conn.execute("PRAGMA table_info(rolls)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if "is_perfect" not in columns:
                    conn.execute("ALTER TABLE rolls ADD COLUMN is_perfect INTEGER")
                    print("Kolumn 'is_perfect' har lagts till")
                
                if "is_fumble" not in columns:
                    conn.execute("ALTER TABLE rolls ADD COLUMN is_fumble INTEGER")
                    print("Kolumn 'is_fumble' har lagts till")
            except Exception as e:
                print(f"Varning vid kontroll av kolumner: {e}")
    
    def start_session(self, description: Optional[str] = None) -> str:
        """
        Startar en ny spelsession och returnerar sessions-ID:t.
        Skapar ett unikt ID baserat på tidsstämpel.
        """
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, start_time, description) VALUES (?, ?, ?)",
                (self.current_session, datetime.now(), description)
            )
        return self.current_session
    
    def end_session(self) -> None:
        """
        Avslutar den aktiva sessionen genom att sätta en sluttid.
        """
        if self.current_session:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE sessions SET end_time = ? WHERE session_id = ?",
                    (datetime.now(), self.current_session)
                )
            self.current_session = None
    
    def log_roll(self, user_id: str, user_name: str, command_type: str,
                 num_dice: int, sides: int, roll_values: List[int],
                 modifier: int = 0, target: Optional[int] = None,
                 success: Optional[bool] = None, is_perfect: Optional[bool] = None,
                 is_fumble: Optional[bool] = None) -> None:
        """
        Loggar ett tärningskast i databasen med all relevant information.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Kontrollera tabellstruktur
                cursor = conn.execute("PRAGMA table_info(rolls)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Förbered grundläggande värden
                basic_values = [
                    datetime.now(),
                    self.current_session,
                    user_id,
                    user_name,
                    command_type,
                    num_dice,
                    sides,
                    modifier,
                    target,
                    1 if success else 0 if success is not None else None,
                    json.dumps(roll_values)
                ]
                
                # Skapa SQL för standardkolumner
                sql = """
                    INSERT INTO rolls (
                        timestamp, session_id, user_id, user_name, command_type,
                        num_dice, sides, modifier, target, success, roll_values
                """
                
                # Kontrollera om perfekt/fummel-kolumner finns
                if "is_perfect" in columns and "is_fumble" in columns:
                    sql += ", is_perfect, is_fumble"
                    basic_values.extend([
                        1 if is_perfect else 0 if is_perfect is not None else None,
                        1 if is_fumble else 0 if is_fumble is not None else None
                    ])
                
                # Avsluta SQL-satsen
                sql += ") VALUES (" + ", ".join(["?"] * len(basic_values)) + ")"
                
                # Utför frågan
                conn.execute(sql, basic_values)
        except Exception as e:
            print(f"Fel vid loggning av tärningskast: {e}")
    def get_session_stats(self, session_id: Optional[str] = None) -> Dict:
        """
        Hämtar detaljerad statistik för en session. Om inget session_id anges 
        används den aktiva sessionen. Funktionen aggregerar data för alla
        användare i kanalen under sessionen.
        """
        session_id = session_id or self.current_session
        if not session_id:
            return {"error": "No session specified and no active session"}

        with sqlite3.connect(self.db_path) as conn:
            # Aktivera dictionary factory för enklare resultathantering
            conn.row_factory = sqlite3.Row
            
            # Grundläggande sessionsinfo med användarantal och totalt antal kast
            session_info = conn.execute("""
                SELECT 
                    start_time,
                    end_time,
                    description,
                    (SELECT COUNT(DISTINCT user_id) FROM rolls WHERE session_id = ?) as unique_players,
                    (SELECT COUNT(*) FROM rolls WHERE session_id = ?) as total_rolls
                FROM sessions 
                WHERE session_id = ?
            """, (session_id, session_id, session_id)).fetchone()

            if not session_info:
                return {"error": "Session not found"}

            # Statistik per spelare med totalt antal kast och framgångsfrekvens
            player_stats = conn.execute("""
                SELECT 
                    user_name,
                    COUNT(*) as total_rolls,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures,
                    ROUND(AVG(CASE WHEN success = 1 THEN 1 WHEN success = 0 THEN 0 END) * 100, 1) as success_rate
                FROM rolls 
                WHERE session_id = ? 
                GROUP BY user_id, user_name
                ORDER BY total_rolls DESC
            """, (session_id,)).fetchall()

            # Statistik per kommandotyp (roll, ex, count)
            command_stats = conn.execute("""
                SELECT 
                    command_type,
                    COUNT(*) as uses,
                    ROUND(AVG(CASE WHEN success = 1 THEN 1 WHEN success = 0 THEN 0 END) * 100, 1) as success_rate
                FROM rolls 
                WHERE session_id = ?
                GROUP BY command_type
                ORDER BY uses DESC
            """, (session_id,)).fetchall()

            # Mest använda tärningskombinationerna
            dice_stats = conn.execute("""
                SELECT 
                    num_dice || 'd' || sides as dice_type,
                    COUNT(*) as uses
                FROM rolls 
                WHERE session_id = ?
                GROUP BY num_dice, sides
                ORDER BY uses DESC
                LIMIT 5
            """, (session_id,)).fetchall()
            
            # Försök att hämta statistik för perfekta slag och fummel
            try:
                perfect_fumble_stats = None
                # Kontrollera om kolumnerna finns
                cursor = conn.execute("PRAGMA table_info(rolls)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if "is_perfect" in columns and "is_fumble" in columns:
                    perfect_fumble_stats = conn.execute("""
                        SELECT
                            SUM(CASE WHEN is_perfect = 1 THEN 1 ELSE 0 END) as total_perfect,
                            SUM(CASE WHEN is_fumble = 1 THEN 1 ELSE 0 END) as total_fumble,
                            user_name,
                            SUM(CASE WHEN is_perfect = 1 THEN 1 ELSE 0 END) as user_perfect,
                            SUM(CASE WHEN is_fumble = 1 THEN 1 ELSE 0 END) as user_fumble
                        FROM rolls
                        WHERE session_id = ? AND command_type = 'ex'
                        GROUP BY user_id, user_name
                        ORDER BY user_perfect DESC, user_fumble ASC
                        LIMIT 5
                    """, (session_id,)).fetchall()
            except Exception as e:
                print(f"Fel vid hämtning av perfekt/fummel-statistik: {e}")
                perfect_fumble_stats = None

            # Sammanställ all statistik i ett strukturerat format
            stats_dict = {
                "session_info": {
                    "start_time": session_info['start_time'],
                    "end_time": session_info['end_time'],
                    "description": session_info['description'],
                    "unique_players": session_info['unique_players'],
                    "total_rolls": session_info['total_rolls']
                },
                "player_stats": [{
                    "name": row['user_name'],
                    "total_rolls": row['total_rolls'],
                    "successes": row['successes'] or 0,
                    "failures": row['failures'] or 0,
                    "success_rate": row['success_rate'] or 0
                } for row in player_stats],
                "command_stats": [{
                    "command": row['command_type'],
                    "uses": row['uses'],
                    "success_rate": row['success_rate']
                } for row in command_stats],
                "popular_dice": [{
                    "type": row['dice_type'],
                    "uses": row['uses']
                } for row in dice_stats]
            }
            
            # Lägg till perfekt/fummel-statistik om den finns
            if perfect_fumble_stats is not None:
                total_perfect = 0
                total_fumble = 0
                
                perfect_fumble_player_stats = []
                for row in perfect_fumble_stats:
                    total_perfect += row['user_perfect'] or 0
                    total_fumble += row['user_fumble'] or 0
                    
                    if row['user_perfect'] > 0 or row['user_fumble'] > 0:
                        perfect_fumble_player_stats.append({
                            "name": row['user_name'],
                            "perfect_rolls": row['user_perfect'] or 0,
                            "fumble_rolls": row['user_fumble'] or 0
                        })
                
                stats_dict["ex_special_stats"] = {
                    "total_perfect": total_perfect,
                    "total_fumble": total_fumble,
                    "player_stats": perfect_fumble_player_stats
                }
            
            return stats_dict

    def get_player_stats(self, user_id: str, session_id: Optional[str] = None) -> Dict:
        """
        Hämtar detaljerad statistik för en specifik spelare under en session.
        Fokuserar på spelarens senaste tärningskast och framgångsfrekvens.
        """
        session_id = session_id or self.current_session
        if not session_id:
            return {"error": "No session specified and no active session"}

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Kontrollera om kolumnerna finns
            cursor = conn.execute("PRAGMA table_info(rolls)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Baskolumner för alla versioner
            select_columns = "timestamp, command_type, num_dice, sides, modifier, target, success, roll_values"
            
            # Lägg till perfekt/fummel om de finns
            if "is_perfect" in columns:
                select_columns += ", is_perfect"
            if "is_fumble" in columns:
                select_columns += ", is_fumble"
            
            # Hämta spelarens tärningskast, sorterade efter tidsstämpel
            query = f"""
                SELECT 
                    {select_columns}
                FROM rolls 
                WHERE session_id = ? AND user_id = ?
                ORDER BY timestamp DESC
            """
            
            rolls = conn.execute(query, (session_id, user_id)).fetchall()
            
            # Generera return-objektet med hänsyn till vilka kolumner som finns
            roll_list = []
            for r in rolls:
                roll_dict = {
                    "timestamp": r['timestamp'],
                    "command": r['command_type'],
                    "dice": f"{r['num_dice']}d{r['sides']}{'+' + str(r['modifier']) if r['modifier'] > 0 else str(r['modifier']) if r['modifier'] < 0 else ''}",
                    "target": r['target'],
                    "success": r['success'],
                    "values": json.loads(r['roll_values'])
                }
                
                # Lägg till perfekt/fummel om de finns och det är ett ex-kommando
                if r['command_type'] == 'ex' or r['command_type'] == 'secret_ex':
                    if "is_perfect" in columns and r['is_perfect'] is not None:
                        roll_dict["is_perfect"] = bool(r['is_perfect'])
                    if "is_fumble" in columns and r['is_fumble'] is not None:
                        roll_dict["is_fumble"] = bool(r['is_fumble'])
                
                roll_list.append(roll_dict)
            
            # Hämta summering av perfekt/fummel om kolumnerna finns och det är ex-kommandon
            ex_special_stats = None
            if "is_perfect" in columns and "is_fumble" in columns:
                try:
                    pf_stats = conn.execute("""
                        SELECT
                            COUNT(*) as total_rolls,
                            SUM(CASE WHEN is_perfect = 1 THEN 1 ELSE 0 END) as perfect_rolls,
                            SUM(CASE WHEN is_fumble = 1 THEN 1 ELSE 0 END) as fumble_rolls
                        FROM rolls
                        WHERE session_id = ? AND user_id = ? AND command_type = 'ex'
                    """, (session_id, user_id)).fetchone()
                    
                    if pf_stats and pf_stats['total_rolls'] > 0:
                        ex_special_stats = {
                            "total_rolls": pf_stats['total_rolls'],
                            "perfect_rolls": pf_stats['perfect_rolls'] or 0,
                            "fumble_rolls": pf_stats['fumble_rolls'] or 0,
                            "perfect_rate": round((pf_stats['perfect_rolls'] or 0) * 100 / pf_stats['total_rolls'], 1) if pf_stats['total_rolls'] > 0 else 0,
                            "fumble_rate": round((pf_stats['fumble_rolls'] or 0) * 100 / pf_stats['total_rolls'], 1) if pf_stats['total_rolls'] > 0 else 0
                        }
                except Exception as e:
                    print(f"Fel vid hämtning av spelarens perfekt/fummel-statistik: {e}")
            
            result = {"rolls": roll_list}
            
            if ex_special_stats:
                result["ex_special_stats"] = ex_special_stats
                
            return result

    def get_all_time_stats(self) -> Dict:
        """
        Hämtar permanent statistik för alla spelare och sessioner genom tiderna.
        Returnerar aggregerade mätvärden för hela databasen.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Kontrollera om kolumnerna finns
            cursor = conn.execute("PRAGMA table_info(rolls)")
            columns = [column[1] for column in cursor.fetchall()]
            has_perfect_fumble = "is_perfect" in columns and "is_fumble" in columns
            
            # Hämta grundläggande statistik
            basic_stats = conn.execute("""
                SELECT 
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(DISTINCT user_id) as total_players,
                    COUNT(*) as total_rolls,
                    (SELECT COUNT(*) FROM rolls WHERE success = 1) as total_successes,
                    (SELECT COUNT(*) FROM rolls WHERE success = 0) as total_failures,
                    ROUND(AVG(CASE WHEN success = 1 THEN 1 WHEN success = 0 THEN 0 END) * 100, 1) as avg_success_rate
                FROM rolls
            """).fetchone()
            
            # Lägg till perfekt/fummel-statistik om kolumnerna finns
            ex_perfect_fumble_counts = None
            if has_perfect_fumble:
                ex_perfect_fumble_counts = conn.execute("""
                    SELECT
                        SUM(CASE WHEN is_perfect = 1 THEN 1 ELSE 0 END) as total_perfect,
                        SUM(CASE WHEN is_fumble = 1 THEN 1 ELSE 0 END) as total_fumble
                    FROM rolls
                    WHERE command_type = 'ex'
                """).fetchone()
            
            # Hämta statistik per spelare
            player_stats_query = """
                SELECT 
                    user_name,
                    COUNT(*) as total_rolls,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures,
                    ROUND(AVG(CASE WHEN success = 1 THEN 1 WHEN success = 0 THEN 0 END) * 100, 1) as success_rate
            """
            
            # Lägg till ytterligare ex-statistik om kolumnerna finns
            if has_perfect_fumble:
                player_stats_query += """,
                    (SELECT SUM(CASE WHEN is_perfect = 1 THEN 1 ELSE 0 END) FROM rolls WHERE user_id = r.user_id AND command_type = 'ex') as ex_perfect_rolls,
                    (SELECT SUM(CASE WHEN is_fumble = 1 THEN 1 ELSE 0 END) FROM rolls WHERE user_id = r.user_id AND command_type = 'ex') as ex_fumble_rolls
                """
                
            player_stats_query += """
                FROM rolls r
                GROUP BY user_id, user_name
                ORDER BY total_rolls DESC
            """
            
            player_stats = conn.execute(player_stats_query).fetchall()
            
            # Hämta statistik per kommandotyp 
            command_stats = conn.execute("""
                SELECT 
                    command_type,
                    COUNT(*) as uses,
                    ROUND(AVG(CASE WHEN success = 1 THEN 1 WHEN success = 0 THEN 0 END) * 100, 1) as success_rate
                FROM rolls 
                GROUP BY command_type
                ORDER BY uses DESC
            """).fetchall()
            
            # Mest använda tärningskombinationerna
            dice_stats = conn.execute("""
                SELECT 
                    num_dice || 'd' || sides as dice_type,
                    COUNT(*) as uses
                FROM rolls 
                GROUP BY num_dice, sides
                ORDER BY uses DESC
                LIMIT 10
            """).fetchall()
            
            # Längsta kontinuerliga sessionerna (tid)
            longest_sessions = conn.execute("""
                SELECT 
                    session_id,
                    description,
                    start_time,
                    end_time,
                    julianday(end_time) - julianday(start_time) as duration_days,
                    COUNT(*) as roll_count
                FROM sessions
                JOIN rolls USING (session_id)
                WHERE end_time IS NOT NULL
                GROUP BY session_id
                ORDER BY duration_days DESC
                LIMIT 5
            """).fetchall()
            
            # Bygg resultatet
            result = {
                "basic_stats": {
                    "total_sessions": basic_stats['total_sessions'],
                    "total_players": basic_stats['total_players'],
                    "total_rolls": basic_stats['total_rolls'],
                    "total_successes": basic_stats['total_successes'] or 0,
                    "total_failures": basic_stats['total_failures'] or 0,
                    "avg_success_rate": basic_stats['avg_success_rate'] or 0
                },
                "player_stats": [{
                    "name": row['user_name'],
                    "total_rolls": row['total_rolls'],
                    "successes": row['successes'] or 0,
                    "failures": row['failures'] or 0,
                    "success_rate": row['success_rate'] or 0
                } for row in player_stats],
                "command_stats": [{
                    "command": row['command_type'],
                    "uses": row['uses'],
                    "success_rate": row['success_rate']
                } for row in command_stats],
                "popular_dice": [{
                    "type": row['dice_type'],
                    "uses": row['uses']
                } for row in dice_stats],
                "longest_sessions": [{
                    "session_id": row['session_id'],
                    "description": row['description'],
                    "duration_days": row['duration_days'],
                    "roll_count": row['roll_count']
                } for row in longest_sessions]
            }
            
            # Lägg till ex_special_stats om det finns
            if has_perfect_fumble and ex_perfect_fumble_counts:
                result["ex_special_stats"] = {
                    "total_perfect_rolls": ex_perfect_fumble_counts['total_perfect'] or 0,
                    "total_fumble_rolls": ex_perfect_fumble_counts['total_fumble'] or 0
                }
                
                # Lägg till perfekt/fummel för varje spelare om de har ex-kommandon
                for i, player in enumerate(result["player_stats"]):
                    if i < len(player_stats):  # Säkerhetscheck för att undvika index out of range
                        perfect_rolls = player_stats[i]['ex_perfect_rolls'] if has_perfect_fumble and 'ex_perfect_rolls' in player_stats[i].keys() else 0
                        fumble_rolls = player_stats[i]['ex_fumble_rolls'] if has_perfect_fumble and 'ex_fumble_rolls' in player_stats[i].keys() else 0
                        
                        if perfect_rolls or fumble_rolls:
                            player["ex_perfect_rolls"] = perfect_rolls or 0
                            player["ex_fumble_rolls"] = fumble_rolls or 0
            
            return result    
    def get_player_all_time_stats(self, user_id: str) -> Dict:
        """
        Hämtar permanent statistik för en specifik spelare över alla sessioner.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Kontrollera om kolumnerna finns
            cursor = conn.execute("PRAGMA table_info(rolls)")
            columns = [column[1] for column in cursor.fetchall()]
            has_perfect_fumble = "is_perfect" in columns and "is_fumble" in columns
            
            # Grundläggande statistik
            basic_stats_query = """
                SELECT 
                    COUNT(*) as total_rolls,
                    COUNT(DISTINCT session_id) as participated_sessions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as total_successes,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as total_failures,
                    ROUND(AVG(CASE WHEN success = 1 THEN 1 WHEN success = 0 THEN 0 END) * 100, 1) as success_rate,
                    MAX(timestamp) as last_roll
            """
            
            if has_perfect_fumble:
                basic_stats_query += """,
                    (SELECT COUNT(*) FROM rolls WHERE user_id = ? AND command_type = 'ex') as ex_total_rolls,
                    (SELECT SUM(CASE WHEN is_perfect = 1 THEN 1 ELSE 0 END) FROM rolls WHERE user_id = ? AND command_type = 'ex') as ex_perfect_rolls,
                    (SELECT SUM(CASE WHEN is_fumble = 1 THEN 1 ELSE 0 END) FROM rolls WHERE user_id = ? AND command_type = 'ex') as ex_fumble_rolls
                """
                basic_stats = conn.execute(basic_stats_query + " FROM rolls WHERE user_id = ?", 
                                          (user_id, user_id, user_id, user_id)).fetchone()
            else:
                basic_stats = conn.execute(basic_stats_query + " FROM rolls WHERE user_id = ?", 
                                          (user_id,)).fetchone()
            
            # Statistik per kommandotyp
            command_stats = conn.execute("""
                SELECT 
                    command_type,
                    COUNT(*) as uses,
                    ROUND(AVG(CASE WHEN success = 1 THEN 1 WHEN success = 0 THEN 0 END) * 100, 1) as success_rate
                FROM rolls 
                WHERE user_id = ?
                GROUP BY command_type
                ORDER BY uses DESC
            """, (user_id,)).fetchall()
            
            # Populära tärningar
            dice_stats = conn.execute("""
                SELECT 
                    num_dice || 'd' || sides as dice_type,
                    COUNT(*) as uses
                FROM rolls 
                WHERE user_id = ?
                GROUP BY num_dice, sides
                ORDER BY uses DESC
                LIMIT 5
            """, (user_id,)).fetchall()
            
            # "Lyckligaste" tärningskombinationen 
            lucky_dice = conn.execute("""
                SELECT 
                    num_dice || 'd' || sides as dice_type,
                    COUNT(*) as uses,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    ROUND((SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 1) as success_rate
                FROM rolls 
                WHERE user_id = ? AND success IS NOT NULL
                GROUP BY num_dice, sides
                HAVING COUNT(*) >= 5  -- Minst 5 kast för att räknas
                ORDER BY success_rate DESC
                LIMIT 1
            """, (user_id,)).fetchone()
            
            # "Olycksaligaste" tärningskombinationen
            unlucky_dice = conn.execute("""
                SELECT 
                    num_dice || 'd' || sides as dice_type,
                    COUNT(*) as uses,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    ROUND((SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 1) as success_rate
                FROM rolls 
                WHERE user_id = ? AND success IS NOT NULL
                GROUP BY num_dice, sides
                HAVING COUNT(*) >= 5  -- Minst 5 kast för att räknas
                ORDER BY success_rate ASC
                LIMIT 1
            """, (user_id,)).fetchone()
            
            # Hämta användarnamn
            user_name = conn.execute("""
                SELECT user_name FROM rolls WHERE user_id = ? LIMIT 1
            """, (user_id,)).fetchone()
            
            if not basic_stats or basic_stats['total_rolls'] == 0:
                return {"error": f"No statistics found for user {user_id}"}
            
            result = {
                "user_id": user_id,
                "user_name": user_name['user_name'] if user_name else "Unknown",
                "basic_stats": {
                    "total_rolls": basic_stats['total_rolls'],
                    "participated_sessions": basic_stats['participated_sessions'],
                    "total_successes": basic_stats['total_successes'] or 0,
                    "total_failures": basic_stats['total_failures'] or 0,
                    "success_rate": basic_stats['success_rate'] or 0,
                    "last_roll": basic_stats['last_roll']
                },
                "command_stats": [{
                    "command": row['command_type'],
                    "uses": row['uses'],
                    "success_rate": row['success_rate']
                } for row in command_stats],
                "popular_dice": [{
                    "type": row['dice_type'],
                    "uses": row['uses']
                } for row in dice_stats],
                "lucky_dice": {
                    "type": lucky_dice['dice_type'] if lucky_dice else None,
                    "uses": lucky_dice['uses'] if lucky_dice else 0,
                    "success_rate": lucky_dice['success_rate'] if lucky_dice else 0
                },
                "unlucky_dice": {
                    "type": unlucky_dice['dice_type'] if unlucky_dice else None,
                    "uses": unlucky_dice['uses'] if unlucky_dice else 0,
                    "success_rate": unlucky_dice['success_rate'] if unlucky_dice else 0
                }
            }
            
            # Lägg till ex_special_stats om det finns
            if has_perfect_fumble and 'ex_total_rolls' in basic_stats.keys() and basic_stats['ex_total_rolls'] > 0:
                result["ex_special_stats"] = {
                    "total_rolls": basic_stats['ex_total_rolls'],
                    "perfect_rolls": basic_stats['ex_perfect_rolls'] or 0,
                    "fumble_rolls": basic_stats['ex_fumble_rolls'] or 0,
                    "perfect_rate": round((basic_stats['ex_perfect_rolls'] or 0) * 100 / basic_stats['ex_total_rolls'], 1),
                    "fumble_rate": round((basic_stats['ex_fumble_rolls'] or 0) * 100 / basic_stats['ex_total_rolls'], 1)
                }
            
            return result        