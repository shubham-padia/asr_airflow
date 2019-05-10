import psycopg2
try:
        db = psycopg2.connect("dbname='watcher' user='watcher' host='localhost' password='yeshallnotpass'")
except:
        exit(1)

        exit(0)
