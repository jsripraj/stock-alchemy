from dotenv import load_dotenv
import os
import config

load_dotenv()

def insert(table: str, headers: list, data: list[list]):
    cnx = mysql.connector.connect(host=config.MYSQL_HOST, database=config.MYSQL_DATABASE, user=os.getenv("MYSQL_USER"), password=os.getenv("MYSQL_PASSWORD"))
    cursor = cnx.cursor()
    first_line = f"INSERT INTO {table} "
    second_line = f'({", ".join(header for header in headers)}) '
    for row in data:
        third_line = f'VALUES ({", ".join(["%s"] * len(headers))})'
        command = first_line + second_line + third_line
        cursor.execute(command, row)

    cnx.commit()
    cursor.close()
    cnx.close()