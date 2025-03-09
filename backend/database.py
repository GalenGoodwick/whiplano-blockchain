import mysql.connector
from mysql.connector import Error
import uuid
from backend.logging_config import logging_config  # Import the configuration file
import logging.config
from fastapi import FastAPI, HTTPException
from datetime import datetime
from backend import storage
import os 
import dotenv
import time
dotenv.load_dotenv()
logging.config.dictConfig(logging_config)
logger = logging.getLogger("database")

class DatabaseManager:
    def __init__(self, host, user, password, database):
        """
        Initializes a new instance of the DatabaseManager class.

        Parameters:
        - host (str): The host address of the MySQL database.
        - user (str): The username for connecting to the MySQL database.
        - password (str): The password for connecting to the MySQL database.
        - database (str): The name of the MySQL database.

        Returns:
        - None

        Raises:
        - HTTPException: If there is an error connecting to the MySQL database.
        """
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )

            if self.connection.is_connected():
                logger.info("Successfully connected to the database")
        except Error as e:
            logger.error(f"Error: {e}")
            self.connection = None
            raise HTTPException(status_code=400, detail=str(e))
            self.connection = None
    async def conn(self):
        """
        Attempts to reconnect to the database. 

        Returns:
        - None

        Raises:
        - HTTPException: If there is an error connecting to the MySQL database.
        """
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("DATABASE_HOST"),
                user=os.getenv("DATABASE_USERNAME"),
                password=os.getenv("DATABASE_PASSWORD"),
                database =os.getenv("DATABASE_NAME")
            )
            if self.connection.is_connected():
                logger.info("Successfully connected to the database")
                return True

        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        return False
    async def attempt_connection(self):
        connection = False
        for i in range(5):
            connection = await self.conn()
            if connection: 
                
                return True
            else:
                logger.error("Connection failed, trying again in 3.")
                time.sleep(3)
        return connection
            


    async def add_asset(self, values):
        """
        Adds a new asset (token) to the user's wallet in the database.

        This function checks if a database connection is available. If not, it prints a message indicating the lack of a
        database connection and returns early. If a connection is available, it attempts to insert a new asset record into
        the 'trs' table. The 'wallet_id' is set to the same value as 'user_id'.

        Parameters:
        - user_id (int): The unique identifier of the user who owns the asset.
        - trs_id (str): The unique identifier of the asset (token).
        - collection_id (str): The identifier of the collection to which the asset belongs.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor()
            query = f"INSERT INTO trs (user_id,trs_id,collection_name,creator) VALUES (%s, %s,%s,%s)"

            cursor.executemany(query, values)
            self.connection.commit()
            logger.info(f"Tokens added succesfully. ")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
    async def get_owner(self, trs_id):
        """
        Retrieves the owner of a specific asset (token) from the database.

        This function connects to the database, checks if a connection is available, and then retrieves the owner's user ID
        from the 'trs' table based on the provided asset (token) ID. If the connection is not available, it prints a message
        indicating the lack of a database connection.

        Parameters:
        - trs_id (str): The unique identifier of the asset (token).

        Returns:
        - dict: A dictionary containing the owner's user ID if the asset exists in the database.
                 If the asset does not exist or there is an error, returns None.
        """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT user_id FROM trs WHERE trs_id = %s"
            cursor.execute(query, (trs_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            return None
    
    async def add_transaction(self, buyer_transaction_number, trs_id, buyer_id, seller_id, amount, number):
        """
        Adds a new transaction record to the database.

        This function connects to the database, checks if a connection is available, and then inserts a new transaction record
        into the 'transactions' table. If the connection is not available, it prints a message indicating the lack of a
        database connection.

        Parameters:
        - transaction_number (str): The unique identifier of the transaction.
        - trs_id (str): The unique identifier of the asset (token) involved in the transaction.
        - buyer_id (int): The unique identifier of the buyer.
        - seller_id (int): The unique identifier of the seller.
        - amount (float): The amount of the transaction.
        - number (int): The quantity of assets (tokens) involved in the transaction.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor()
            transaction_number = str(uuid.uuid4())
            query = f"INSERT INTO transactions (buyer_transaction_number,transaction_number,trs_id,buyer_id,seller_id,amount,number) VALUES (%s,%s, %s,%s,%s,%s)"
            values = (buyer_transaction_number,transaction_number, trs_id, buyer_id, seller_id, amount, number)
            cursor.execute(query, values)
            self.connection.commit()
            logger.info(f"Transaction {transaction_number} and buyer transaction number {buyer_transaction_number} added successfully")
            
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def modify_transaction(self, transaction_number,status):
        """
    Modifies a transaction record in the database.

    Parameters:
    - transaction_number (str): The unique identifier of the transaction.
    - status (str): The new status of the transaction.

    Returns:
    - None

    Raises:
    - HTTPException: If there is an error updating the transaction record.
        """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor()
            query = f"UPDATE transactions set status = %s  where transaction_number = %s "
            values = (status,transaction_number)
            cursor.execute(query, values)
            self.connection.commit()
            logger.info(f"Transaction {transaction_number} modified successfully to {status}")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
    async def transfer_asset(self, user_id, trs_id):
        """
        Transfers an asset (token) from the current owner to a new user in the database.

        This function connects to the database, checks if a connection is available, and then updates the 'user_id' field
        in the 'trs' table to the new user's ID. The function also prints a success message if the transfer is successful,
        or an error message if an error occurs.

        Parameters:
        - user_id (int): The unique identifier of the new owner of the asset.
        - trs_id (str): The unique identifier of the asset (token) to be transferred.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor()
            query = f"UPDATE trs SET user_id = %s WHERE trs_id = %s"

            cursor.execute(query, (user_id, trs_id))
            logger.info(f"Transferred TRS {trs_id} to {user_id}.")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    async def close_connection(self):
        """
        Closes the database connection if it is currently open.

        This function checks if a database connection is available and if it is connected.
        If both conditions are met, it closes the connection and prints a success message.

        Parameters:
        - None

        Returns:
        - None
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
            
    async def add_trs(self,number, mint_address, collection_name, token_account_address,creator_id):
        """
        Adds a new token to the database.

        This function connects to the database, checks if a connection is available, and then inserts a new token record
        into the 'collections' table. If the connection is not available, it prints a message indicating the lack of a
        database connection.

        Parameters:
    
        - mint_address (str): The address of the mint that created the token.
        - collection_name (str): The name of the collection to which the token belongs.
        - token_account_address (str): The address of the token account associated with the token.
        - creator_id (int): The unique identifier of the creator of the token.
        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor()
            batch_values = []
            trs_id_values = []
            for i in range(number):
                trs_id = uuid.uuid4().int
                batch_values.append((str(trs_id), collection_name, str(mint_address), str(token_account_address),str(creator_id)))
                trs_id_values.append((creator_id,trs_id,collection_name,creator_id))
            query = f"INSERT INTO collections (trs_id, collection_name, mint_address, token_account_address,creator_id) VALUES (%s, %s, %s, %s,%s)"
            cursor.executemany(query,batch_values)
            self.connection.commit()
            await self.add_asset(trs_id_values)       
            logger.info(f"Added {number} tokens of collection name {collection_name} to {creator_id}.")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
 
    async def get_wallet(self, user_id):
        """
        Retrieves the wallet of a user from the database.

        This function connects to the database, checks if a connection is available, and then retrieves the wallet
        of a user from the 'trs' table based on the provided user ID. If the connection is not available, it prints a
        message indicating the lack of a database connection. If the user does not exist, it prints a message indicating
        the user not found.

        Parameters:
        - user_id (int): The unique identifier of the user.

        Returns:
        - list: A list of dictionaries containing the asset (token) details in the user's wallet.
                 If the user does not exist or there is an error, returns None.
        """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        elif not await self.get_user(user_id):
            logger.info(f"User not found {user_id}")
            return None
        else:
            try: 
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT trs_id,collection_name FROM trs WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                result = cursor.fetchall()
                logger.info(f"Returned wallet of user {user_id}")
                return result
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                return None
            finally: 
                cursor.close()
    
    async def get_collection_data(self,name):
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM collection_data WHERE name = %s"
            cursor.execute(query, (name,))
            result = cursor.fetchall()
            return result
        except Error as e:

            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        finally:
            cursor.close()

    async def get_approved_transactions(self,buyer_transaction_id):
        """
    Retrieves the approved transactions for a buyer from the database.

    Parameters:
    buyer_transaction_id (str): The unique identifier of the buyer.

    Returns:
    list: A list of dictionaries representing the approved transactions. Each dictionary contains the transaction details.

    Raises:
    HTTPException: If there is an error connecting to the database or retrieving the transactions.
    """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM transactions WHERE buyer_id = %s AND status = %s"
            cursor.execute(query, (buyer_transaction_id, "initiated"))
            result = cursor.fetchall()
            logger.info(f"Retrieved approved transactions for buyer {buyer_transaction_id}")
            return result
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            return None
        finally:
            cursor.close()
        
    
    
    async def approve_initiated_transactions(self,buyer_transaction_id):
        """
    Retrieves the approved transactions for a buyer from the database.

    Parameters:
    buyer_transaction_id (str): The unique identifier of the buyer.

    Returns:
    list: A list of dictionaries representing the approved transactions. Each dictionary contains the transaction details.

    Raises:
    HTTPException: If there is an error connecting to the database or retrieving the transactions.
    """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "UPDATE transacations SET status = 'approved' where buyer_id = %s AND status = 'initiated'"
            cursor.execute(query, (buyer_transaction_id, ))
            result = cursor.fetchall()
            logger.info(f"Approved initiated transactions for buyer {buyer_transaction_id}")
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            return None
        finally:
            cursor.close()
        return


    
    async def finish_approved_transactions(self,buyer_transaction_id):
        """
    Finishes the approved transactions for a buyer from the database.

    Parameters:
    buyer_transaction_id (str): The unique identifier of the buyer.

    Returns:
    bool: True if the transactions were successfully finished, False otherwise.

    Raises:
    HTTPException: If there is an error connecting to the database or finishing the transactions.
    """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "UPDATE transacations SET status = 'finished' where buyer_id = %s AND status = 'initiated'"
            cursor.execute(query, (buyer_transaction_id, ))
            result = cursor.fetchall()
            logger.info(f"Finished approved transactions for buyer {buyer_transaction_id}")
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            return None
        finally:
            cursor.close()
        return
    
    async def get_wallet_by_collection(self,user_id,collection_id):
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        elif not await self.get_user(user_id):
            logger.error(f"User not found {user_id}")
            return None
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT trs_id, collection_name FROM trs WHERE user_id = %s AND collection_name = %s"
                cursor.execute(query, (user_id, collection_id))
                result = cursor.fetchall()
                logger.info(f"Selected wallet by collection {collection_id}, from {user_id}")
                return result
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                return None
            finally:
                cursor.close()
       
    async def get_mint_address(self,collection_name):
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT mint_address FROM collections WHERE collection_name = %s"
                cursor.execute(query, (collection_name,))
                result = cursor.fetchall()
                logger.info(f"Retrieved Mint Address by collection {collection_name}")
                return result
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                
                return None
            finally:
                cursor.close()
        return 
    
    
    async def get_creator(self,collection_name):
        """
    Retrieves the creator id of a collection from the database.

    Parameters:
    collection_name (str): The name of the collection.

    Returns:
    str: The creator id of the collection.

    Raises:
    HTTPException: If there is an error connecting to the database or retrieving the creator id.
        """
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT creator_id FROM collections WHERE collection_name = %s LIMIT 1"

                cursor.execute(query, (collection_name,))
                result = cursor.fetchall()
                logger.info(f"Retrieved Creator id of collection {collection_name}")
                return result['creator_id']
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                return None
            finally:
                cursor.close()
        return

    async def get_token_account_address(self, collection_name):
        if not self.connection:
            logger.critical("No database connection")
            e = await self.attempt_connection()
            if not e:
                raise HTTPException(status_code = 501, detail = "Could not connect to the database. Please try later. ")
            else:
                raise HTTPException(status_code=502, detail="Your request couldn't be processed, please try again. ")
        else:
            try: 
                cursor = self.connection.cursor(dictionary=True)
                query = "select * from collections where collection_name = %s"
                cursor.execute(query,(collection_name,))
                logger.info(f"Fetched token account address of collection : {collection_name}")
                result = cursor.fetchall()
                token_account_address = result[0]["token_account_address"]
                return token_account_address
                
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()