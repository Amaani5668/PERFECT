from pymongo import MongoClient
import urllib.parse
import certifi

username = 'sam007'
password = 'Das@007'  # Replace with your actual password

# Encode the username and password using urllib.parse.quote_plus
encoded_username = urllib.parse.quote_plus(username)
encoded_password = urllib.parse.quote_plus(password)

# Construct the connection string
connection_string = f"mongodb+srv://{encoded_username}:{encoded_password}@das.nfmj12w.mongodb.net/?retryWrites=true&w=majority"

# Create a MongoClient instance with the certificate file
client = MongoClient(connection_string, tlsCAFile=certifi.where())

# Test the connection
try:
    client.admin.command('ping')
    print("Connected to MongoDB Atlas!")
except Exception as e:
    print(f"An error occurred: {e}")
