# AE SD
import pymysql.cursors


TABLE_TO_COLUMS = {
    'basicinfo':('USER_ID', 'FIRST_NAME', 'LAST_NAME', 'BIRTH', 'CITY', 'STREET'),
    'courses':('COURSE_NAME', 'COURSE_DATE', 'COURCE_NAME', 'COURCE_CERTIFICATE'),
    'events':('EVENT_NAME', 'EVENT_DATE', 'EVENT_INFO','EVENT_BARCODE'),
    'identification':('USER_MAIL', 'USER_PASSWORD')}

class MdaappDB(object):
    """docstring for MdaappDB"""
    def __init__(self):
        self.host = '172.25.129.191'
        self.username = 'root'
        self.password = 'Password1!'
        self.database = 'mdaappdb'
        self.connection = pymysql.connect(host=self.host,
                             user=self.username,
                             password=self.password,
                             database=self.database,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


    def __execute_command(self, command_string):
        try:
            with self.connection.cursor() as cursor:
                # Create a new record
                cursor.execute(command_string)
            
                result = cursor.fetchone()
                print(result)   
            # self.connection is not autocommit by default. So you must commit to save
            # your changes.
            self.connection.commit()
            return result
        except Exception as e:
            print(f"Unexpected {e=}, {type(e)=}")
            return False

    def __insert_data(self, table_name, arguments):
        """
        arguments must be a tuple or a list
        """
        if table_name in TABLE_TO_COLUMS:
            command = "INSERT INTO `{table}` (`{columes}`) VALUES ('{data}')".format(table=table_name ,columes="`,`".join(TABLE_TO_COLUMS[table_name]), data="','".join(arguments))
            print(command)
            return self.__execute_command(command)
        return False

    def __delete_user(self, user_id):
        """
        arguments must be a tuple or a list
        """
        command = "DELETE FROM basicinfo where USER_ID = {0}".format(user_id)
        print(command)
        self.__execute_command(command)

        command = "DELETE FROM identification where USER_ID = {0}".format(user_id)
        print(command)
        self.__execute_command(command)

    def __get_ident_id_by_mail(self, user_mail):
        command = "SELECT * FROM identification where USER_MAIL = '{0}'".format(user_mail)
        print(command)
        result = self.__execute_command(command)
        return result

    def get_user_data_by_mail(self, user_mail):
        user_id = self.__get_ident_id_by_mail(user_mail)['USER_ID']
        command = "SELECT * FROM basicinfo where USER_ID = '{0}'".format(user_id)
        print(command)
        result = self.__execute_command(command)
        return result

    def is_user_exists(self, user_mail):
        """
        if exists return user data else False
        """
        result = self.__get_ident_id_by_mail(user_mail)
        if result == None:
            print("Doesnt exist")
            return False
        return result

    def add_user(self, user_mail, user_password, user_firstname, user_lastname, user_birth, user_city, user_street):
        """
        user_birth = 'DD-MM-YY'
        """
        user_data = self.is_user_exists(user_mail)
        if user_data:
            print("user already exist")
            return False

        result = self.__insert_data('identification', (user_mail, user_password))
        if result is False:
            return False
        else:
            user_id = self.is_user_exists(user_mail)['USER_ID']
            print(user_id)

            result = self.__insert_data('basicinfo', (str(user_id), user_firstname, user_lastname, user_birth, user_city, user_street))
            if result is False:
                self.__delete_user(user_id)
                return False
            return user_id

    def check_user_creds(self, user_mail, user_password):
        result = self.is_user_exists(user_mail)
        if result:
            if result['USER_PASSWORD'] == user_password:
                return True
        return False
        
    def get_max_user_id():
        pass
    
    def get_event_data():
        pass

    def log_event():
        pass