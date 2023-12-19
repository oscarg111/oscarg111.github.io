from flask import Flask, render_template, request
import requests
from pyzbar.pyzbar import decode
import urllib.request
import simplejson
from geopy.geocoders import Photon
from geopy.extra.rate_limiter import RateLimiter
from PIL import Image

# global variables
barcode_spider_api_key = "f4f9fe42f4d67f5f9070"
material_array = ""
wms_url = "https://www.google.com/search?q="
earth911_url = 'http://api.earth911.com/'
earth911_api_key = 'c21ff4fe1052dda1'
wms_product_search = '+"packaging material"'
geocoder = Photon(user_agent="geoapiExercises")
geocode = RateLimiter(geocoder.geocode, min_delay_seconds=1, return_value_on_exception=None)
barcode_data = ""
keep_scan_bar = True
file = None
keep_input = "y"
app = Flask(__name__)


# Your existing Terra code here...
class Material:
    def __init__(self, type_m, product, descrip, link):
        self.type_m = type_m
        self.product = product
        self.guess = 0
        self.descrip = descrip
        self.link = link

    def __str__(self):
        return str(self.product)

    def serialize(self):
        return f"{self.type_m};{','.join(self.product)};{self.descrip};{self.link}"


# Using "guess" to predict material of product
def similaritySort(database):
    mostLikelyMaterial = Material("dummy", "", "", "")

    # Runs through the database and collects the material object with the highest guess value
    for i in database:
        if (i.guess > mostLikelyMaterial.guess):
            mostLikelyMaterial = i

    return mostLikelyMaterial


def scan_barcodes(frame):
    global barcode_data
    global keep_scan_bar
    img = decode(frame)
    print(img)
    barcodes = img

    for barcode in barcodes:
        # Print the barcode data to understand its structure
        print("Barcode Data:", barcode.data)

        # Extract the barcode data and draw a rectangle around it
        barcode_data = barcode.data.decode('utf-8')
        barcode_data = barcode_data[1:]
        keep_scan_bar = False

    return frame


# Searches for a UPC code in material database, if no exact match found, guesses based on brand occurence
def findMaterials(upc, database):
    match = False
    for i in database:  # Running through all the materials in the database

        if i is None:
            continue
        for k in i.product:  # Running through each one of the barcodes stored inside the material
            if (upc[0:6] in k):
                i.guess += 1
                match = True

                if (upc == k):
                    print("Item Found")
                    print(
                        "Your item was found to be: " + i.type_m + ".\n" + i.descrip + "\nFor more information visit: " + i.link)
                    return i.type_m

    if (match == True):
        print("We could not find an exact match in our database, searching for similar products . . .")
        print("We found products that shares manufacturing information")
        mostLM = similaritySort(database)
        print(
            "Your 'similar' item was found to be: " + mostLM.type_m + ".\n" + mostLM.descrip + "\nFor more information visit: " + mostLM.link)
        return mostLM.type_m


    else:
        string = ""
        print("After extensive searching, your product was not found.")
        y_n = input("Would you like to update the database with your object (y/n): ")

        while (y_n != 'y'):

            if (y_n == 'n'):
                return
            print("Please enter a valid option")
            y_n = input("Would you like to update the database with your object (y/n): ")

        largestIndex = 0
        for j in database:
            string += (str(database.index(j)) + ": " + j.type_m + " \n ")
            largestIndex = database.index(j)
        print(string)

        while (True):
            try:
                materialChosen = input("Please choose a number from the above list:  ")
                materialChosen = int(materialChosen)
                if ((materialChosen >= 0) and (materialChosen <= largestIndex)):
                    mat = database[materialChosen]

                    if (mat.product == None):
                        mat.product = [upc]

                    else:
                        mat.product.append(upc)

                    database[materialChosen] = mat
                    updateDatabase(database)
                    print("Thanks for your help, your barcode has been inputted")
                    print(mat)
                    return mat

                else:
                    print("Out of range")
            except:
                print("Invalid input")


# Read materials.txt and upcbar.txt

# Convert materials.txt into a list of material objects with linked information about it
def loadDatabase():
    # Store each line of materials.txt as an index of materials array
    with open("materials2.txt", 'r') as file:
        materials = (file.readlines())
        # file.close()

    # initialize array of material objects
    objectList = [None] * len(materials)
    match = False

    # For each line in materials
    for i in materials:

        # Seperating each piece of data from a line
        materialsSplit = i.split(';')

        if (materialsSplit[0] == "\n"):
            continue
        # Store barcode(s) in item object
        try:
            upcSplit = materialsSplit[1].split(',')

            # Creating an material object using the information given materialsSplit
            item = Material(materialsSplit[0], upcSplit, materialsSplit[2], materialsSplit[3])

        # If no barcode in material array
        except:
            print(materialsSplit)
            item = Material(materialsSplit[0], None, materialsSplit[2], materialsSplit[3])

        # objectList is the array of materials objects generated from materials.txt
        # objectList is index matched with the lines from the "materials" array
        objectList[materials.index(i)] = item

    return objectList


def updateDatabase(database):
    with open("materials.txt", 'w') as file:
        for material in database:
            file.write(material.serialize())

        # materials = (file.readlines())


def BarcodeProduct(upc, api):
    barcode_url = "https://api.barcodespider.com/v1/lookup"

    barcode_query = {"upc": upc}

    barcode_headers = {
        'token': api,
        'Host': "api.barcodespider.com",
        'Accept-Encoding': "gzip, deflate",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
    }
    try:
        barcode_response = requests.request("GET", barcode_url, headers=barcode_headers, params=barcode_query)

        barcode_api_response = barcode_response.json()

        product_data = barcode_api_response['item_attributes']
        manu = product_data['manufacturer']
        brand = product_data['brand']
        product_description = product_data['description'] + " " + product_data['category'] + " " + product_data[
            'title'] + " " + product_data['parent_category'] + " " + product_data['category']
        print("Your product was found to be: " + product_data['title'])
        # product_description = str(product_data)
        # product_data
        return {"manu": manu, "brand": brand, "description": upc, "temp1": product_data['description']}
    except(KeyError):
        return {"manu": "00000", "brand": "00000", "description": "00000", "temp1": "00000"}
    except(requests.ConnectionError):
        return {"manu": "11111", "brand": "11111", "description": "11111", "temp1": "11111"}


# Earth911 Search
def searchEarth911(item, city_name):
    item = item.replace(' ', '+')

    location = geocode(city_name)
    if location is not None:
        lat, lon = location.latitude, location.longitude
    else:
        print(f"City '{city_name}' not found or geocoding error.")
        return 0

    earth911_query = (
            earth911_url + 'earth911.searchMaterials?api_key=' + earth911_api_key + '&query=' + item + '&max_results=1')

    text = urllib.request.urlopen(earth911_query).read()
    result = simplejson.loads(text)
    if 'error' in result:
        return 0

    found_material = result['result']
    found_materialv2 = found_material[0]
    found_materialv3 = found_materialv2['material_id']
    print("Searching Database, please wait, the system takes about a minute to search.")
    earth911_location_query = (
            earth911_url + 'earth911.searchLocations?api_key=' + earth911_api_key + '&latitude=' + str(
        lat) + '&longitude=' + str(lon) + '&material_id=' + str(found_materialv3))

    text = urllib.request.urlopen(earth911_location_query).read()

    result = simplejson.loads(text)
    if 'error' in result:
        return 0
    else:
        print("")
        for res in result['result']:
            # try:
            # print(res['description'])

            return "\nFound a result:\n" + "Location: " + res['description'] + "\nDistance from city center: " + str(
                res['distance']) + "mi.\nIs it curbside?: " + str(res['curbside'])

            # except:
            # print("")


database = loadDatabase()


@app.route('/')
def index():
    return render_template('index.html')


# @app.route('/upload', methods=['POST'])
@app.route('/upload', methods=['POST'])
def upload():
    global file
    global barcode_data

    if 'file' not in request.files:
        return render_template('index.html', error='No file part')

    file = request.files['file']

    if file.filename == '':
        return render_template('index.html', error='No selected file')

    try:
        # Attempt to open the image file
        img = Image.open(file)
        # Convert the image to a format supported by pyzbar (e.g., RGB)
        # img = img.convert('RGB')
        # Get the decoded barcodes
        scan_barcodes(img)

        barspiresult = BarcodeProduct(barcode_data, barcode_spider_api_key)
        materials = findMaterials(barcode_data, database)
        earth911_results = searchEarth911(materials, request.form['city_name'])

        return render_template('results.html', filename=file.filename, barcode_data=barcode_data,
                               materials=materials, earth911_results=earth911_results)

    except Exception as e:
        # Handle any exceptions (e.g., invalid image format)
        print(f"Error processing image: {e}")
        return render_template('index.html', error='Error processing image')


if __name__ == '__main__':
    app.run(debug=True)
