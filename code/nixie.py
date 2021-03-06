# Nixie Pi clock, v1.1
import datetime, random, time
import RPi.GPIO as GPIO
import feedparser
import commands

# ***************************
# User configurable options.
# ************
bbcWeather = "2643029"  # BBC weather location code, for temp/humidity and pressure. 
maxDotBright = 70       # Maximum brightness (0 - 100) of INS-1 dots.
onTime = 6              # Time to turn display back on (display goes off at midnight). Set to 0 for never off

# Wiring below, to K155ID1 IC ABCD inputs (A is LSB, D is MSB).
# Each sub-list goes from MSB to LSB (D to A). 

# Top-left most (hrs tens)
# A: GPIO11 B:6 C:13 D:5
lamp1 = [5, 13, 6, 11]

# Top-middle (hrs units)
# A: GPIO27  B:10 C:9 D: 22
lamp2 = [22, 9, 10, 27]

# Top-right most (mins tens)
# A: GPIO2 B:4 C:17 D: 3
lamp3 = [3, 17, 4, 2]

# Bottom-left most (minutes units)
# A: GPIO12 B:20 C:21 D: 16
lamp4 = [16, 21, 20, 12]

# Bottom-middle (seconds tens)
# A: GPIO24 B: 8  C: 7  D: 25
lamp5 = [25, 7, 8, 24]

# Bottom-right IC (nearest female connector to Pi; seconds units)
# A: GPIO18 B: 14 C: 15 D: GPIO23
lamp6 = [23, 15, 14, 18]

# Bottom pair of dots
bDots = 26

# Top pair of dots
tDots = 19

lamps = [lamp3, lamp2, lamp1, lamp4, lamp5, lamp6]
GPIO.setmode(GPIO.BCM) # The 5V pin in the top-left corner is referred to as 2.
GPIO.setwarnings(False)

for lamp in lamps:
    for pin in lamp:
        GPIO.setup(pin, GPIO.OUT)

GPIO.setup(bDots, GPIO.OUT)
GPIO.setup(tDots, GPIO.OUT)
pbDots = GPIO.PWM(bDots, 60)
ptDots = GPIO.PWM(tDots, 60)

weatherOk = False   # Variable to remember whether the weather worked the last time we tried to get it.
# ****************************
# Functions start here
# ********************

def weather(areaCode):
    # areaCode is the BBC Weather code (from the desired region's URL).
    # Picks up BBC humidity and temperature data, then shows on the tubes.
    # Returns True if the BBC weather is rendered to the screen correctly.
    url = "http://weather-broker-cdn.api.bbci.co.uk/en/observation/rss/" + areaCode
    global ptDots, pbDots, weatherOk

    try:
        NewsFeed = feedparser.parse(url)
        entry = NewsFeed.entries[0]
        weatherString = entry.description
        tempStart = weatherString.find(" ") + 1
        tempEnd = weatherString.find("C") - 1
        temperature = int(weatherString[tempStart:tempEnd])

        # humidStart = weatherString.find("Humidity: ") + 9
        # humidEnd = weatherString.find("%")
        # humidity = int(weatherString[humidStart:humidEnd])

        # NOTE: If not taking a feed from a sense hat, uncomment the above
        # and comment down to and including the .close() line below.
        f = open('/home/pi/hFile.txt')
        humidity = 0
        for line in f:
            line = line.rstrip()
            humidity = str(int(float(line)))

        f.close()
        
        #print("Temp: " + str(temperature) + ". H:" + str(humidity) + ".")
        weatherOk =  True
        pbDots.start(0)
        ptDots.start(0)
        
        showNum()
        showNum(str(humidity), 'l')
        showNum(str(abs(temperature)), 'r')
        return True
    except:
        # No weather data available.
        weatherOk = False
        return False

def pressure():
    # Parses a .txt file (deposited automatically in /home/pi/) that contains the last 24 hrs of air pressure data.
    # If the SenseHat pi is on, we'll get live air pressure data dropped in every 7.5 mins or so.
    # Returns True if this works sucessfully. 
    global ptDots, pbDots, weatherOk
    pressure = 0000
    
    try:    
        f = open('/home/pi/pFile.txt')
        
        for line in f:
            line = line.rstrip()
            pressure = str(int(float(line)))
        f.close()
    except:
        print("Problem reading pressure log file")
        
    # Show the air pressure on the display.
    showNum()
    showNum(pressure, 'c')
    pbDots.start(0)
    ptDots.start(0)
    weatherOk =  True
    return True

def oldPressure():
    # ALTERNATIVE VERSION 
    # If required, swap the names of this function and the 'pressure()' function to get BBC Weather instead.
    url = "http://weather-broker-cdn.api.bbci.co.uk/en/observation/rss/" + areaCode
    global ptDots, pbDots, weatherOk

    try:
        NewsFeed = feedparser.parse(url)
        entry = NewsFeed.entries[0]
        weatherString = entry.description
        pressStart = weatherString.find("Pressure: ") + 10
        pressEnd = weatherString.find("mb")
        pressure = weatherString[pressStart:pressEnd]

        if len(pressure) < 4:
            pressure = "0" + pressure
            
        weatherOk =  True
        pbDots.start(0)
        ptDots.start(0)

        # Show the air pressure on the display.
        showNum()
        showNum(pressure, 'c')
        return True
    except:
        # No weather data available.
        weatherOk = False
        return False
    
def showOutput(hrs, mins, secs):
    # Function to illuminate tubes
    # Pass in three pairs of values to appear.
    # Leading zeros are added automatically.
    currDigit = 1
    timeArr = [hrs, mins, secs]
    
    for item in timeArr:
        if item > 9 and item < 100:
            lightUp(currDigit, item // 10)
	    lightUp(currDigit + 1, item - ((item // 10) * 10))
        elif item > 2000:
            # Deals with the clock displaying the date.
            num = item - 2000
            lightUp(currDigit, num // 10)
	    lightUp(currDigit + 1, num - ((num // 10) * 10))

            global ptDots, pbDots
            global maxDotBright
            pbDots.start(maxDotBright)
            ptDots.start(0)
        elif item >= 0:
	    lightUp(currDigit, 0)
	    lightUp(currDigit + 1, item)
        else:
            # If we're here, we've been sent something like -1.
            lightUp(currDigit, -1)
	    lightUp(currDigit + 1, -1)

        currDigit = currDigit + 2

def slideOff(hrs, mins, secs):
    # Makes current time 'slide off' the display.
    timeArr = [hrs, mins, secs]
    y = 6
    for x in range(1, -7, -1):
        currDigit = x
        for item in timeArr:
            if item > 9 and item < 100:
                lightUp(currDigit, item // 10)
	        lightUp(currDigit + 1, item - ((item // 10) * 10))
            elif item > 2000:
                # Deals with the clock displaying the date.
                num = item - 2000
                lightUp(currDigit, num // 10)
	        lightUp(currDigit + 1, num - ((num // 10) * 10))
            else:
	        lightUp(currDigit, 0)
	        lightUp(currDigit + 1, item)
                
            currDigit = currDigit + 2
            
        # Blank the right-most digits.
        for n in range(6, y, -1):
            lightUp(n, 10)
        y = y - 1
        
        time.sleep(0.1)

    # Then, do something similar to slide the date onto the display.
    now = datetime.datetime.now()
    day = now.day
    month = now.month
    year = now.year
    timeArr = [day, month, year]

    for x in range(6, 0, -1):
        currDigit = x
        for item in timeArr:
            if item > 9 and item < 100:
                lightUp(currDigit, item // 10)
	        lightUp(currDigit + 1, item - ((item // 10) * 10))
            elif item > 2000:
                # Deals with the clock displaying the date.
                num = item - 2000
                lightUp(currDigit, num // 10)
	        lightUp(currDigit + 1, num - ((num // 10) * 10))
            else:
	        lightUp(currDigit, 0)
	        lightUp(currDigit + 1, item)
                
            currDigit = currDigit + 2
        
        time.sleep(0.1)    

def cycleNums():
    # Get each tube to show 10 different digits at (pseudo)random, over the space of 1sec.
    print("Cathode protection cycle (old style) starting...")
    
    for x in range(20):
        for y in range(1, 7):
            lightUp(y, random.randint(0, 9))
            
	time.sleep(0.05)
        
    print("Cathode protection cycle complete.")

def cycleNums2():
    # Get each tube to show 10 different digits at (pseudo)random, over the space of 1sec.
    print("Cathode protection cycle (new style) starting...")

    now = datetime.datetime.now()
    hrs = now.hour
    mins = now.minute
    secs = now.second + 1  # It takes about a second to do the animation.
    timeArr = [hrs, mins, secs]
    
    startAt = 1
    endAt = 2

    for digits in range(9):
        for x in range(10):
            currDigit = 1    
            for item in timeArr:
                if item > 9 and item < 100 and currDigit < endAt:
                    lightUp(currDigit, item // 10)
	            lightUp(currDigit + 1, item - ((item // 10) * 10))
                else:
                    if currDigit < endAt:
	                lightUp(currDigit, 0)
	                lightUp(currDigit + 1, item)
                currDigit = currDigit + 2
            
            for lamp in range(startAt, endAt):
                lightUp(lamp, random.randint(0, 9))
	    time.sleep(0.015)
            
        endAt = endAt + 1
        if endAt > 4:
            startAt = startAt + 1

    print("Cathode protection cycle complete.")

def lightUp(lamp, numToShow):
    global lamps
    # Pass in which Nixie tube (1-6) and the digit to show (0 to 9)
    # Showing a digit where the value is >9 turns it off, when using the K155ID1 IC.
    if lamp > 0 and lamp < 7:
        lamp = lamp - 1

        if numToShow >= 0 and numToShow <= 9:
            binNum = str(bin(numToShow))[2:]   # binNum will be something like '10'
            #print("numToShow is " + str(numToShow) + " on lamp " + str(lamp) + ".")

            while len(binNum) < 4:  # Add leading zeroes to get it to 4 bits.
                binNum = '0' + binNum 
        
            GPIO.output(lamps[lamp][0], int(binNum[0]))
            GPIO.output(lamps[lamp][1], int(binNum[1]))
            GPIO.output(lamps[lamp][2], int(binNum[2]))
            GPIO.output(lamps[lamp][3], int(binNum[3]))    
            # print("Lamp " + str(lamp + 1) + " showing " + str(numToShow))
        else:
            GPIO.output(lamps[lamp][0], 1)
            GPIO.output(lamps[lamp][1], 1)
            GPIO.output(lamps[lamp][2], 1)
            GPIO.output(lamps[lamp][3], 1)
            # Turn the lamp in question off if < 0 or > 9 is received.
            
def showNum(inputString = '------', alignment = 'r', leadingZeros = False):
    # Function to show up to 6 digits on the display.
    # inputString - e.g. '99--42', '123'. Hyphens denote to leave off.
    # alignment - 'l', 'c' or 'r'.
    # leadingZeros - fill display with zeros. Only relevant for 'r' align.
    # NOTE: Calling with no parameters will blank the display. 
    strLen = len(str(inputString))
    
    if alignment == 'c':
        if strLen == 6:
            startFrom = 1
        elif strLen == 5:
            startFrom = 2
        elif strLen == 4:
            startFrom = 2
        elif strLen == 3:
            startFrom = 3
        elif strLen == 2:
            startFrom = 3
        elif strLen == 1:
            startFrom = 4
        else:
            startFrom = 4

        currDigit = 0

        for x in range(startFrom, startFrom + strLen):
            if inputString[currDigit] != '-':
                lightUp(x, int(inputString[currDigit]))
            else:
                lightUp(x, -1)

            currDigit = currDigit + 1
    elif alignment == 'l':
        startFrom = 1
        currDigit = 0

        for x in range(startFrom, strLen + 1):
            if inputString[currDigit] != '-':
                lightUp(x, int(inputString[currDigit]))
            else:
                lightUp(x, -1)

            currDigit = currDigit + 1
    else:
        if leadingZeros == True:
            for x in range (1, 7):
                lightUp(x, 0)
                
        startFrom = 7 - strLen
        currDigit = 0

        for x in range(startFrom, 7):
            if inputString[currDigit] != '-':
                lightUp(x, int(inputString[currDigit]))
            else:
                lightUp(x, -1)
                
            currDigit = currDigit + 1
        
        
def showIP():
    # Show IP address on startup, so we can get in.
    address = commands.getoutput('hostname -I')
    addEnd = address.find(" ") +1
    address = address[:addEnd]
    octs = []
    for i in range(4):
        addEnd = address.find(".")
        octs.append(address[0:addEnd])
        address = address[addEnd + 1:]

    showNum()
    showNum(octs[0], 'l')
    showNum(octs[1], 'r')
    time.sleep(3)

    showNum()
    showNum(octs[2], 'l')
    showNum(octs[3], 'r')
    time.sleep(3)


# *********************************
# Main loop starts here
# ***************

# Countdown. Here for several reasons...
# 1. Serves to ensure an IP address has been grabbed
# 2. Avoids any PWM flicker, as most of the boot-up heavy CPU load is done.
# 3. Warms the INS-1 tubes by driving them at full brightness for a few seconds. Seems to make them less likely to flicker.
pbDots.start(100)
ptDots.start(100)

for n in range(9, -1, -1):
    for x in range(1, 7):
        lightUp(x, n)
        time.sleep(0.6)

try:
    # Try and show the IP address on the display.
    # Useful in case the user needs to SSH into it in future.
    pbDots.start(0)
    ptDots.start(0)
    showIP()
except:
    print("No IP available")
    
while True:
    now = datetime.datetime.now()
    hrs = now.hour
    mins = now.minute
    secs = now.second
    milli = float(now.strftime('%f'))
    
    # Debug output...
    # print("Time: " + str(hrs) + ":" + str(mins) + ":" + str(secs))
    # print("Date: " + str(day) + "/" + str(month) + "/" + str(year))
    # print("----")

    if hrs >= onTime:
        if secs==15:
            # Cycle the tubes through different digits to prevent cathode poisoning.
            pbDots.start(0)
            ptDots.start(0)
            slideOff(hrs, mins, secs)
        elif secs==20:
            pbDots.start(0)
            ptDots.start(0)
            cycleNums2()
        elif secs >= 16 and secs <= 20:
            # Show the date at quarter past each minute for 5s
	    showOutput (now.day, now.month, now.year)
        elif (secs==45 or secs == 52) and weatherOk == True:
            pbDots.start(0)
            ptDots.start(0)
            cycleNums()
        elif secs > 45 and secs <52:
            # Show the local humidity (left) and temperature (right)
            if secs > 45 and secs < 49:
                ok = weather(bbcWeather)
            else:
                ok = pressure()   # Add bbcWeather as parameter if using BBC weather.
                time.sleep(3.5)   # This prevents a little flicker when the pi has to reload the .txt file over and over.     
            if ok == False:
                # If the RSS feed isn't working, just keep showing the time,
	        showOutput(hrs, mins, secs)
                # Deal with the dots...
                duty = int((milli / 999999) * maxDotBright)
                if milli < 500000:
                    pbDots.start(duty)
                    ptDots.start(duty)
                else:
                    pbDots.start(maxDotBright - duty)
                    ptDots.start(maxDotBright - duty)
        else:
            # Show the time on the tubes.
	    showOutput(hrs, mins, secs)
            # Deal with the dots...
            duty = int((milli / 999999) * maxDotBright)
            if milli < 500000:
                pbDots.start(duty)
                ptDots.start(duty)
            else:
                pbDots.start(maxDotBright - duty)
                ptDots.start(maxDotBright - duty)
    else:
        # If the display is off, turn the dots and digits off too. 
        pbDots.start(0)
        ptDots.start(0)
        lightUp(1, -1)
        lightUp(2, -1)
        lightUp(3, -1)
        lightUp(4, -1)
        lightUp(5, -1)
        lightUp(6, -1)
