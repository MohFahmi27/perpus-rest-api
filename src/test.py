import requests

BASE_URL = "http://127.0.0.1:5000/"

response = requests.put(BASE_URL + "buku/add", {
    "isbn": "fkjsldfj", "judul_buku": "How to Stop Something2", "pengarang": "Slihian", "tahun_terbit" : "2021", "qty_buku": 2
}) 
print(response.json())