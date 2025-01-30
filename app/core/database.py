from pymongo import MongoClient

from app.core.config import config


class MongoDatabase:
    """
    Handles MongoDB connections and collections.
    """

    def __init__(self):
        self.client = self.check_mongo_connection()
        self.db = self.client[config.MONGO_DATABASE]
        self.users_collection = self.db["Users"]
        self.lessons_collection = self.db["Lessons"]
        self.students_collection = self.db["Students"]

    def check_mongo_connection(self):
        """
        Checks the MongoDB connection using the configured URI.
        """
        if not config.MONGO_CLUSTER_URL:
            raise KeyError("MongoDB URI is not set/loaded correctly.")

        try:
            client = MongoClient(config.MONGO_CLUSTER_URL)
            client.admin.command('ping')
            print("Connected to MongoDB successfully!")
            return client
        except Exception as e:
            print(f"MongoDB connection failed: {str(e)}")
            raise Exception(f"MongoDB connection failed: {str(e)}")


mongo_db = MongoDatabase()