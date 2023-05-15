import requests

url = 'https://fl-api-rest.herokuapp.com/get_/categories/jcdelangel'

data = requests.get(url)

if data.status_code == 200: # ok
	datas = data.json().get('message', [])
	for gia,data in enumerate(datas):
		print(f'\n\n{gia}: CATEGORY: {data["idCat"]} -> {data["category"]}')
		for gia3, data3 in enumerate(data["subcategories"]):
			print(f'{gia3}: {data3["idSCat"]}->{data3["subcategory"]}')
