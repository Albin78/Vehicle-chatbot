# from pymongo import MongoClient
# from dotenv import load_dotenv
# import os
# import time

# load_dotenv()

# client = MongoClient(os.getenv("MONGO_URI"))
# db = client[os.getenv("MONGO_DB")]
# collection = db[os.getenv("MONGO_COLLECTION")]

# # Ensure index exists (safe to call multiple times)
# collection.create_index([("imei", 1), ("last_updated", 1)])

# imei = 354018114615747

# start = time.time()
# print("Starting Mongo fetch")

# cursor = collection.find({"imei": imei}) \
#                    .sort("last_updated", 1)

# for record in cursor:
#     pass   # process here

# print("Mongo fetch done")
# print("Time taken: ", time.time() - start)


# import requests

# url = "https://api.girfalco.sa/v2/vehicle/vehicleDetailsByIMEI?IMEI=354018113220879"

# payload = {}
# headers = {
#   'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiU3VwZXJBZG1pbiIsImlkIjo1MTEsImVtYWlsIjoic3VwZXJhZG1pbkB2bXMuY29tIiwidHlwZSI6MSwiY29tcGFueWlkIjowLCJWR3JvdXAiOiIiLCJDQWRtaW4iOjAsIkFzc2V0VHJhY2siOiIwIiwiQmluVHJhY2siOiIwIiwiVmVoaWNsZVRyYWNrIjoiMSIsIkRlZmF1bHRUcmFjayI6IjEiLCJjb21wYW55SURzIjpbXSwidm1zQWRtaW4iOnRydWUsIm9yaWdpbkNvZGUiOiJzYSIsImlhdCI6MTc0NzI5MTQ5NCwiZXhwIjoxODA3MjkxNDk0LCJzdWIiOiJzdXBlcmFkbWluQHZtcy5jb20ifQ.oJF6lvl-vU8f4DdBXR4EIUI_U6MmLAvR4-prZPWE5Qoj6QThUfLXmbHpPRpnjGCr6j8u-urDTzVRV_N1w61DDJY52sUe-rlYoeIhCHkiLP63tbZn_rZ8tYtInouuZ9lTQIFIbuOrBZDy4ARojjaC5AzsXKxhHmubjEEFFefI8xpW_oIoGSBRgHYfsVKTPcXVY-blHI8AQD4RK85ZrH5GUJrl8hf2MonO9gBEJXNTQy1XmTS7yJNA-cdJKGF7NOmpnf8y8jCbqgN599PptWpMdqE7RVdu84B2oCjUx5jnTbTKQIjWUITn-ncMiD8Wdp9PS7FLE7SP-f1SPdRkZJW3MRaWed5LZ-rzEv8XKrFIkSfBbaxtOfIkKnzZl6iLtBM4Eo5Vrrvq1CRF2yUYANuKUKU7gpJRo-xj5ByPpM5H7Y4nx7NOjHxFAgbEvK3yNh7Fp4fvCqhh20ZlAVB9avZNu_mYJlSBrEpohTRZWKLqHj8NSrSnlkKsDzGs7kzbti0OOVyiz1xAfhustWuXdY7Aa1kHnD7KPLGCdTVqv50KCh7BfJyytqIykebMb3q5TmuCK7laRji8pHrGBtNjnNU95FWWTASinC_b54knRyyaXXUf3HIUZec2BwRQRWWsM--qyJMSFfQ09DaKWsYdZE2jLyWt2pXx1eTKcpUWJDBVu9I'
# }

# response = requests.request("GET", url, headers=headers, data=payload)

# print(response.text)

# from app.config import settings

# print(settings.BATTERY_API_URL)

