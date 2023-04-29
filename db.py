import sqlite3


class BotDB:

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def add_user(self, user_id):
        self.cursor.execute("INSERT INTO 'users' ('user_id') VALUES (?)", (user_id,))
        return self.conn.commit()

    def get_user_id(self, user_id):
        result = self.cursor.execute("SELECT id FROM users where user_id = ?", (user_id,))
        return result.fetchone()[0]

    def add_record(self, user_id, word):
        self.cursor.execute("INSERT INTO 'records' ('user_id', 'word') VALUES (?, ?)",
                            (self.get_user_id(user_id),
                             word))

        return self.conn.commit()

    def delete_record(self, user_id, word):
        self.cursor.execute("DELETE FROM records where (user_id, word) = (?, ?)",
                            (self.get_user_id(user_id),
                             word))

        return self.conn.commit()

    def get_records(self, user_id):
        c = 0

        info = ''
        m = self.cursor.execute("SELECT * FROM records where user_id = ?", (self.get_user_id(user_id),)).fetchall()

        for i in m:
            c += 1
            info += f"{c}. {i[2]}\n"

        return info

    def close(self):
        self.cursor.close()
        self.conn.close()
