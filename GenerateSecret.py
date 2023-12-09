import os

key = os.urandom(64)
with open(".ctfd_secret_key", "wb") as secret:
    secret.write(key)
    secret.flush()

print("Secret Key Generated:")
print(key, flush=True)
