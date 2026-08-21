import time

class TokenCache:

    def __init__(self):
        self.cache = {}

    def get(self, key):
        if key not in self.cache:
            return None

        token, exp = self.cache[key]
        if time.time() > exp:
            del self.cache[key]
            return None

        return token

    def store(self, key, token, exp):
        self.cache[key] = (token, exp)
