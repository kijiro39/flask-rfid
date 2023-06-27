import pymysql

def conn_db():
    # database connection
    connection = pymysql.connect(host="localhost", port=8889, user="root", passwd="root", database="attendance")
    cursor = connection.cursor()
    # some other statements  with the help of cursor
    # print(connection)
    connection.close()

