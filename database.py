import sqlite3

class Database:
    def __init__(self):
        self.con = sqlite3.connect('wordsets_db.db')
        self.cursor = self.con.cursor()
        self.create_sets_table()
        self.create_words_table()
        self.create_settings_table()
        self.con.commit()

        # check_sets = self.is_table_empty("sets")
        check_settings = self.is_table_empty("settings")

        if check_settings:
            self.cursor.execute("INSERT INTO settings(text_color,init_trigger) VALUES(?,?)", ("Red", 0))



    def create_sets_table(self):
        sets_table = """CREATE TABLE IF NOT EXISTS sets (
        	set_id integer PRIMARY KEY AUTOINCREMENT,
        	name text NOT NULL UNIQUE, 
        	number_of_words integer,
        	settype text,
        	last_time_date TEXT
        ); """

        self.cursor.execute(sets_table)
        self.con.commit()

    def create_words_table(self):
        words_table = """CREATE TABLE IF NOT EXISTS words (
        	id integer PRIMARY KEY AUTOINCREMENT,
        	word text NOT NULL,
        	image text,
        	set_name text,
        	FOREIGN KEY (set_name) REFERENCES sets (name)
        );"""

        self.cursor.execute(words_table)
        self.con.commit()

    def create_settings_table(self):
        settings_table = """CREATE TABLE IF NOT EXISTS settings (
        	id integer PRIMARY KEY AUTOINCREMENT,
        	text_color text,
        	init_trigger int
        );"""

        self.cursor.execute(settings_table)
        self.con.commit()

    def insert_set(self, name, number, settype="words"):
        self.cursor.execute("INSERT INTO sets(name, number_of_words, settype) VALUES(?,?,?)", (name,number, settype))
        self.con.commit()

    def insert_words(self, word, set_name, image=""):
        self.cursor.execute("INSERT INTO words(word, set_name, image) VALUES(?,?,?)", (word,set_name,image))
        self.con.commit()

    def is_table_empty(self, table_name):
        query = self.cursor.execute(f"SELECT * FROM {table_name}").fetchall()

        if len(query) == 0:
            return True
        else:
            return False


    def example_sets(self,languages):
        pojazdy = {"pojazdy 1": ["pojazd", "samochód", "wywrotka", "betoniarka", "karetka", "radiowóz", "wóz strażacki",
                               "limuzyna", "kamper", "furgonetka"],
        "pojazdy 2": ["tir", "ciężarówka", "motor", "rower", "skuter", "autobus", "tramwaj","taksówka", "metro","pociąg"]}

        owoce = {
            "owoce 1": ["banan", "jabłko", "gruszka", "brzoskwinia", "śliwka", "arbuz", "agrest", "winogrona", "morela",
                      "truskawka"],
            "owoce 2": ["malina", "jagody", "wiśnie", "czereśnie", "porzeczki", "grejpfrut","kiwi","poziomki","ananas","jeżyny"]}

        vehicles = {"vehicles 1": ["vehicle", "car", "dumper", "cement mixer", "ambulance", "police car", "fire engine",
                               "limousine", "lorry", "van"],
        "vehicles 2": ["articulated lorry", "camper", "motorcycle", "bicycle", "scooter", "bus", "tram","taxi", "underground","train"]}

        fruits = {
            "fruits 1": ["fruit", "banana", "apple", "pear", "peach", "plum", "watermelon", "gooseberry", "grape", "apricot"],
            "fruits 2": ["strawberry","raspberry", "blueberry", "cherry", "currant", "grapefruit","kiwi","wild strawberry","pineapple","blackberry"]}


        if "Polish" in languages:
            for k,v in pojazdy.items():
                self.insert_set(name=k, number=len(v))
                for word in v:
                    self.insert_words(word,k)

            for k, v in owoce.items():
                self.insert_set(name=k, number=len(v))
                for word in v:
                    self.insert_words(word, k)

        if "English" in languages:
            for k, v in vehicles.items():
                self.insert_set(name=k, number=len(v))
                for word in v:
                    self.insert_words(word, k)

            for k, v in fruits.items():
                self.insert_set(name=k, number=len(v))
                for word in v:
                    self.insert_words(word, k)


    def is_name_exists(self, *set_name):
        return self.cursor.execute("SELECT name FROM sets").fetchall()

    def get_sets(self):
        return self.cursor.execute("SELECT name, number_of_words, settype FROM sets").fetchall()

    def get_words(self, name):
        return self.cursor.execute("SELECT word, image FROM words WHERE set_name=?", (name,)).fetchall()


    def delete_set(self, name):
        self.cursor.execute("DELETE FROM words WHERE set_name=?", (name,))
        self.cursor.execute("DELETE FROM sets WHERE name=?", (name,))
        self.con.commit()


    def update_date(self, name, date):
        self.cursor.execute("UPDATE sets SET last_time_date=? WHERE name=?", (date, name))
        self.con.commit()

    def close_db_connection(self):
        self.con.close()
