import cryptocurrency as CryptoClient

CryptoClient.NODE_NAME = "NODE1"

CryptoClient.app.run(host = "0.0.0.0", port = 5001)