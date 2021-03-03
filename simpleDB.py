
import sqlite3


class SimpleDB(object):
    def __init__(self, file_path):
        self.conn = sqlite3.connect(file_path)
    
    def execute(self, command):
        cursor = self.conn.cursor()
        cursor.execute(command)
        cursor.close()
        self.conn.commit()
    
    def query(self, command):
        cursor = self.conn.cursor()
        cursor.execute(command)
        res = cursor.fetchall()
        cursor.close()
        return res
    
    def iterate(self, command):
        cursor = self.conn.cursor()
        cursor.execute(command)
        while (True):
            res = cursor.fetchone()
            if (res == None):
                break
            yield res
        cursor.close()
    
    def close(self):
        self.conn.close()
