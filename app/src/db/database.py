import psycopg2

from app.utils.logger import logger
from app.config.config import settings


class DataBaseUtil:

    def __init__(self , db_config):
        self.db_config = db_config

        try:
            self.connection = psycopg2.connect(**db_config)

        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
            self.connection = None


    def schema_details(self, schema_name):

        schema_info_context = ""

        connection = self.connection
        cursor = connection.cursor()

        schema_info_context = f"Database Schema: {schema_name}\n"

        try:

            cursor.execute("SELECT table_name from information_schema.tables where table_schema = %s;", (schema_name,))
            tabels_list = cursor.fetchall()

            for table in tabels_list:
                table_name = table[0]
                schema_info_context = f"{schema_info_context}\nTable: {table_name}\n"

                # Adding Columns & Data Types
                cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s;", (table_name,))
                column_list = cursor.fetchall()


                for column in column_list:
                    column_name = column[0]
                    data_type = column[1]
                    schema_info_context = f"{schema_info_context}  Column: {column_name}, Data Type: {data_type}\n"

                # Adding Sample Data
                cursor.execute(f"SELECT * FROM {schema_name}.{table_name} LIMIT 5;")
                sample_data = cursor.fetchall()
                schema_info_context = f"{schema_info_context}  Sample Data:\n"
                for row in sample_data:
                    schema_info_context = f"{schema_info_context}    {row}\n"

        except Exception as e:
            logger.error(f"Error fetching schema details: {e}")
            schema_info_context = f"Error fetching schema details: {e}"

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return schema_info_context


    def execute_sql(self, query):
        cursor = None
        connection = None
        try:
            connection = self.connection
            if not connection:
                return "Error: Database connection is not established."
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            connection.commit()
            return str(result)

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return None

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()




if __name__ == "__main__":
    obj = DataBaseUtil({
        "host" : settings.host,
        "port" : settings.port,
        "user" : settings.user,
        "password" : settings.password,
        "dbname" : settings.database_name
    })

    result = obj.schema_details("public")

    with open("test_schema_details.txt", "w") as f:
        f.write(result)