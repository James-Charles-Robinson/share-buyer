from selenium import webdriver
import json
import datetime
import time

# gets the user settings for the program
def userSettings():

    file = open("usersettings.txt", "r")
    lines = file.readlines()

    userSettings = []
    
    for line in lines:
        line = int(line.split(": ")[1].replace("\n", ""))
        userSettings.append(line)


    return userSettings

# gets the data for the stock
def getData(driver):

    table = driver.find_element_by_class_name(
        "col-md-8")
    rows = table.text.split("\n")
    buyPrice = float(rows[0].split("(GBX) ")[1].split(" Var")[0].replace(",", ""))
    change = float(rows[0].split("(+/-) ")[1].split(" ( ")[0].replace("%", "").replace("+", ""))
    high = float(rows[1].replace("High ", "").split(" Low")[0].replace(",", ""))
    low = float(rows[1].split(" Low ")[1].replace(",", ""))
    sellPrice = float(rows[3].replace("Bid ", "").split(" Offer")[0].replace(",", ""))
    status = rows[4].replace("Trading status ", "").split(" Offer")[0].split(" Special conditions")[0]

    currentData = [buyPrice, change, high, low, sellPrice, status]
    
    return currentData

# adds new data to the stock data text file if its different
def addData(name, newData):

    file = open("stockdata.txt", "r")
    data = json.load(file)
    file.close()
    
    if name not in data:

        data[name] = {"dates": [], "buyPrice": [], "sellPrice": [],
                      "high": [], "low": [], "change": [], "status": []}

    stock = data[name]
        
    if (len(stock["buyPrice"]) == 0 or stock["buyPrice"][-1] != newData[0]
        or stock["sellPrice"][-1] != newData[4]):
        
        time = datetime.datetime.now()
    
        stock["dates"].append(str(time))
        stock["buyPrice"].append(newData[0])
        stock["sellPrice"].append(newData[4])
        stock["high"].append(newData[2])
        stock["low"].append(newData[3])
        stock["change"].append(newData[1])
        stock["status"].append(newData[5])

        data[name] = stock
        
    file = open("stockdata.txt", 'w')
    json.dump(data, file)
    file.close()


def getPreviousData(name):

    file = open("stockdata.txt", "r")
    data = json.load(file)
    file.close()
    if name in data:
        stock = data[name]
        previousData = [stock["dates"], stock["buyPrice"], stock["sellPrice"],
                        stock["high"], stock["low"], stock["change"],
                        stock["status"]]
        return previousData
    else:
        return False

def watchedStocks():
    
    file = open("watchedStocks.txt", "r")
    stocks = file.readlines()
    file.close()
    return stocks

def buyStock(currentData, name, strategyNum, url, money, userSettings):

    file = open("transactions.txt", "r")
    data = json.load(file)
    file.close()

    exsisting = False

    for key, value in data.items():
        if value["Name"] == name and value["Active"] == True:
            exsisting = True
            print("Exsists", name)

    if exsisting == False:

        minSpend = userSettings[2]
        quantity = int(minSpend / currentData[0]) + 1
        time = datetime.datetime.now()
        title = name + str(time)
        data[title] = {'Name': name, "URL": url, 'Date': str(time), 'Strategy': strategyNum,
            'Sell price': currentData[4], 'Buy price': currentData[0],
            'Change': currentData[1], "Quantity": quantity, "Prior Acc Bal": money,
            "Active": True, "Sell Data": {}}

        print(data[title])
        money = round((money - (currentData[0] * quantity))*10) / 10

        file = open("money.txt", "a")
        file.write(str(money) + "\n")
        file.close()

        file = open("transactions.txt", "w")
        json.dump(data, file)
        file.close()
        
    return money

def clearStockData():
    file = open("stockdata.txt", "w")
    file.write("{}")
    file.close()

def sellAll(money, driver):

    file = open("transactions.txt", "r")
    data = json.load(file)
    file.close()

    for key, value in data.items():

        if value["Active"] == True:

            time = datetime.datetime.now()

            driver.get(value["URL"])
            driver.implicitly_wait(5)
            currentData = getData(driver)

            print("Sold", value["Quantity"], value["Name"])
            profit = (value["Buy price"]-currentData[4]) * value["Quantity"]
            print("profit =", profit)
            money = round((money + (currentData[4] * value["Quantity"]))*10)/10

            data[key]["Sell Data"] = {'Date': str(time), 'Strategy': 'sell all',
                                      'Sell price': currentData[4],
                                      'Buy price': currentData[0],
                                      'Change': currentData[1],
                                      "Profit": profit,
                                      "New Bal": money}

            print(data[key]["Sell Data"])
            data[key]["Active"] = "false"

            file = open("money.txt", "a")
            file.write(str(money) + "\n")
            file.close()

                
    file = open("transactions.txt", "w")
    json.dump(data, file)
    file.close()
    return money
   
def quickSell(money, driver, userSettings):

    file = open("transactions.txt", "r")
    data = json.load(file)
    file.close()

    for key, value in data.items():

        if value["Active"] == True:

            time = datetime.datetime.now()
            riskFactor = userSettings[0]
            cutLoss = userSettings[1]

            driver.get(value["URL"])
            driver.implicitly_wait(5)
            currentData = getData(driver)
            if (currentData[4] > (value["Buy price"] * (1 + riskFactor/2000)) or
                currentData[4] < (value["Buy price"] * (1 - cutLoss/500))):

                print("Sold", value["Quantity"], value["Name"])
                profit = (value["Buy price"]-currentData[4]) * value["Quantity"]
                print("profit =", profit)
                money = round((money + (currentData[4] * value["Quantity"]))*10)/10

                data[key]["Sell Data"] = {'Date': str(time), 'Strategy': 'Quick sell',
                                          'Sell price': currentData[4],
                                          'Buy price': currentData[0],
                                          'Change': currentData[1],
                                          "Profit": profit,
                                          "New Bal": money}

                print(data[key]["Sell Data"])
                data[key]["Active"] = "false"

                file = open("money.txt", "a")
                file.write(str(money) + "\n")
                file.close()

                
    file = open("transactions.txt", "w")
    json.dump(data, file)
    file.close()
    return money

def averageChange(lst, frm, to):

    total = 0
    for i in range(frm, to):
        total += ((lst[i+1] - lst[i])/lst[i])
    average = round((total / ((frm - to)*-1))*100000) / 100000
    return average

def medianChange(lst, frm, to):

    values = []
    for i in range(frm, to):
        values.append((lst[i+1] - lst[i])/lst[i])

    median = values[round(len(values)/2)]
    print("median", median)
    return median

def strategy(money, userSettings):

    stocks = watchedStocks()
    driver = webdriver.Firefox()

    for i in range(len(stocks)):
        try:
            name = stocks[i].split(", ")[0]
            url = stocks[i].split(", ")[1].replace("\n", "")

            driver.get(url)
            driver.implicitly_wait(10)

            previousData = getPreviousData(name)
            currentData = getData(driver)
            maxSpend = userSettings[3]
            minSpend = userSettings[2]

            if currentData[5] == "Regular Trading" :
                # if its been going down but then suddenly up
                if previousData != False and money > (minSpend*1.5) and maxSpend > currentData[0]:
                    if len(previousData[0]) > 10 and currentData[1] > 0.15:
                        if (averageChange(previousData[2], -9, -4) < -0.0001 and averageChange(previousData[2], -3, -1) > 0.00014):
                            if (medianChange(previousData[2], -9, -4) < -0.0006 and medianChange(previousData[2], -3, -1) > 0.0006):

                                money = buyStock(currentData, name, 1, url, money, userSettings)

                    # if its consistantly going up
                    if len(previousData[0]) > 10 and currentData[1] > 0.2:
                        if (averageChange(previousData[2], -9, -5) > 0.0001 and averageChange(previousData[2], -5, -1) > 0.00014):
                            if (medianChange(previousData[2], -9, -1) > 0.0006):

                                money = buyStock(currentData, name, 2, url, money, userSettings)

                addData(stocks[i].split(",")[0], currentData)
            else:
                print("Market Close")
                time.sleep(20)
        except:
            pass

    money = quickSell(money, driver, userSettings)
    #sellAll(money, driver)
    driver.close()

#clearStockData()
userSettings = userSettings()

while True:

    file = open("money.txt", "r")
    money = (round(float(file.readlines()[-1].replace("\n", "")) * 10)/10)
    file.close()
    
    money = strategy(money, userSettings)
    print("Loop done")


