from matrix_client.client import MatrixClient

client = MatrixClient("http://localhost:8008")
client.register_with_password(username="tiling_logger", password="catapultons du beurre doux")
client.create_room("events")
