import cv2
import time
import pyautogui
import numpy as np
import win32gui, win32ui, win32con, win32api
from skimage.measure import compare_ssim

'''
This program was designed with the playable subs mod in mind.
The current version of the playable subs mod on Github has 47 enemy subs

** This program was designed and ran on a 24 inch monitor at 1920 x 1080 and the
   ingame resolution was 1920 x 1080.

** The HUD-ZOOM was set to 1.5

** For now the program only works with the Improved Virginia Class due to the varying
   number of torpedo tubes causing the broadband display to be located at different
   heights on screen.

** The program ONLY WORKS in custom game mode due a bug with the playable subs
   mod which changes up the sequence of submarines and civillian vessels in the
   signature tab. Program will not work properly in campaign or quick missions

'''


# Define some constants for the game
NUMBER_ENEMY_SUBS = 47

# Locations for numbers and information on screen
CONTACT_NUMBER_REGION = (1301, 434, 9, 14)
CONDITIONS_TAB_SEA_SURFACE_YPOS = 466
SMALL_IMAGE_HEIGHT = 20
ENEMY_DEPTH_REGION = (1700, CONDITIONS_TAB_SEA_SURFACE_YPOS - SMALL_IMAGE_HEIGHT, 84, 298)
TOP_BROADBAND_REGION = (1496, 504, 337, 88)
BOTTOM_BROADBAND_REGION = (1496, 615, 337, 88)

# Locations for button on screen
SIGNATURE_TAB_SUBMARINE_BUTTON = (1587, 732)

# Players custom bindings
NEXT_CONTACT_BUTTON = 't'
CONFIRM_CONTACT_BUTTON = 'enter'
PREVIOUS_SIGNATURE_CONTACT_BUTTON = ';'
NEXT_SIGNATURE_CONTACT_BUTTON = '#'
CONDITIONS_TAB_BUTTON = 'f5'
SIGNATURE_TAB_BUTTON = 'f6'



# Data structures used for classiying contacts and keeping a tab on them

class ContactList(object):
    def __init__(self):
        self.numberOfContacts = 0
        self.numberOfSubmarines = 0
        self.dict = {} #self.vessels = {}
        self.submarines = {}

    def add(self, contactNumber, dataOnTarget):
        self.dict[contactNumber] = dataOnTarget
        self.numberOfContacts += 1

    def addSubmarine(self, contactNumber, dataOnTarget):
        self.submarines[contactNumber] = dataOnTarget
        self.numberOfSubmarines += 1

    def contains(self, contactNumber):
        return (contactNumber in self.dict)

    def containsSubmarine(self, contactNumber):
        return (contactNumber in self.submarines)

    def get(self, contactNumber):
        return self.dict.get(contactNumber)

    def getSubmarine(self, contactNumber):
        return self.submarines.get(contactNumber)

    def returnAllSubmarineContacts(self):
        return self.submarines.keys()

    def printData(self):
        for key, data in self.dict.items():
            print(key, data.printData())



class Data(object):
    def __init__(self, sierraNumber, bearing, course, speed, range, solution, depth, isSurfaceVessel):
        self.contactNumber = sierraNumber
        self.bearing = bearing
        self.course = course
        self.speed = speed
        self.range = range
        self.solution = solution
        self.depth = depth
        self.isSurfaceVessel = isSurfaceVessel

        self.max_depth = None  # Look into game files for accurate read
        self.changing_course = False
        self.changing_depth = False

    def updateValues(self, sierraNumber, bearing, course, speed, range, solution, depth, isSurfaceVessel):
        self.contactNumber = sierraNumber
        self.bearing = bearing
        self.course = course
        self.speed = speed
        self.range = range
        self.solution = solution
        self.depth = depth
        self.isSurfaceVessel = isSurfaceVessel

    def updateBearing(newBearing):
        self.bearing = newBearing

    def updateCourse(newCourse):
        self.course = newCourse

    def updateSpeed(newSpeed):
        self.speed = newSpeed

    def updateRange(newRange):
        self.range = newRange

    def updateSolution(newSolution):
        self.solution = newSolution

    def updateDepth(newDepth):
        self.depth = newDepth

    def updateIsSurfaceVessel(bool_surface_vessel):
        self.isSurfaceVessel = bool_surface_vessel

    def getVesselData():
        return (self.contactNumber, self.bearing, self.course, self.speed, self.range, self.solution,
                self.depth, self.isSurfaceVessel)

    def getBearing():
        return self.bearing

    def getCourse():
        return self.course

    def getSpeed():
        return self.speed

    def getRange():
        return self.range

    def getSolution():
        return self.solution

    def getDepth():
        return self.depth

    def getIsSurfaceVessel():
        return self.isSurfaceVessel

    def printData(self):
        print("ContactNumber: ",self.contactNumber,"\nBearing: ",self.bearing,"\nCourse: ",self.course,"\nSpeed: ",self.speed,
            "\nRange: ",self.range,"\nSolution: ",self.solution,"\nDepth: ",self.depth,"\nSurface Vessel: ",self.isSurfaceVessel,"\n")



# Run time of around 10 milliseconds
def grab_screen(region=None):

    hwin = win32gui.GetDesktopWindow()

    if region:
            left,top,x2,y2 = region
            width = x2
            height = y2
    else:
        width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

    hwindc = win32gui.GetWindowDC(hwin)
    srcdc = win32ui.CreateDCFromHandle(hwindc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(srcdc, width, height)
    memdc.SelectObject(bmp)
    memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)

    signedIntsArray = bmp.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (height,width,4)

    srcdc.DeleteDC()
    memdc.DeleteDC()
    win32gui.ReleaseDC(hwin, hwindc)
    win32gui.DeleteObject(bmp.GetHandle())

    return cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)


# Has a runtime of 9 - 12 milliseconds
def compareImageToScreenshot(filename, region):

    imageA = cv2.imread(filename)
    imageB = grab_screen(region)

    grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)

    # compute the Structural Similarity Index (SSIM) between the two
    # images, ensuring that the difference image is returned
    (score, diff) = compare_ssim(grayA, grayB, full=True)
    #print("Filename: "+filename+" SSIM: {}".format(score))

    return score


def openConditionsTab():
    pyautogui.press(CONDITIONS_TAB_BUTTON)


def openSignatureTab():
    pyautogui.press(SIGNATURE_TAB_BUTTON)


def cycleToNextContact():
    # Do we need to do a check to see if any contacts exist, or only one contact exists
    pyautogui.press(NEXT_CONTACT_BUTTON)


# Run time of about 10 - 20 milliseconds
# Has problem of detecting surface if no submarine image can be found
def getEnemyDepth(hud_zoom):
    # https://stackoverflow.com/questions/7853628/how-do-i-find-an-image-contained-within-an-image
    # This can only be found in the Conditions tab (F5) and adjusting the depth meter
    method = cv2.TM_SQDIFF_NORMED
    surfaceYpos = CONDITIONS_TAB_SEA_SURFACE_YPOS
    small_image_height = SMALL_IMAGE_HEIGHT
    region = ENEMY_DEPTH_REGION

    # Read the images from the file
    small_image = cv2.imread('images\\submarine_image.png')    # This should be the image of the submarine
    small_image = cv2.cvtColor(small_image, cv2.COLOR_BGR2GRAY)

    large_image = grab_screen(region)   # This should be the grabscreen of the area a submarine can be at
    large_image = cv2.cvtColor(large_image, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(small_image, large_image, method)

    # We want the minimum squared difference
    mn,_,mnLoc,_ = cv2.minMaxLoc(result)

    # Draw the rectangle:
    # Extract the coordinates of our best match
    MPx,MPy = mnLoc
    enemyDepth = ((region[1] + MPy + small_image_height) - surfaceYpos) * (100 / ( 25 / (hud_zoom + 1)))

    return enemyDepth


# Classify a contact quickly as a random submarine
def classifyAsSubmarine():
    pyautogui.click(SIGNATURE_TAB_SUBMARINE_BUTTON[0], SIGNATURE_TAB_SUBMARINE_BUTTON[1])
    pyautogui.press(CONFIRM_CONTACT_BUTTON)
    pyautogui.moveTo(20,20)


# Classify a contact quickly as a random peaceful surface vessel
def classifyAsSurfaceVessel():
    classifyAsSubmarine()
    for i in range(0,5):
        pyautogui.press(PREVIOUS_SIGNATURE_CONTACT)
    pyautogui.press(CONFIRM_CONTACT_BUTTON)


# This is important so that we know which contact we are trying to classify in the signature tab
# This function needs the signature tab to be open
def getContactNumber():
    # Only accounting for 9 contacts right now
    region = CONTACT_NUMBER_REGION
    for digit in range(1, 10):
        if (compareImageToScreenshot('images\\number_'+str(digit)+'.png', region) > 0.75):
            return digit

    return None


# Quickly cycle through all detected contacts and determine if they are a surface vessel
# or submarine... currently only cycles through 9 contacts
def quicklyIdentifyTargets(hud_zoom, numberOfEnemySubsInGame):

    running = True

    # We want to make sure the signature tab is open
    openConditionsTab()
    openSignatureTab()

    contactNumber = getContactNumber()
    original = contactNumber

    while (running):
        if (contactList.contains(contactNumber)):
            pass
        else:
            classifyAsSubmarine()
            openConditionsTab()
            depthOfContact = getEnemyDepth(hud_zoom)

            if (depthOfContact > 40):
                # This is an enemy contact so we are going to focus on it
                # and try to classify it through the broadband display
                compareEnemySubmarineBroadbands(numberOfEnemySubsInGame)
            else:
                # This is probably a surface ship so we are going to quickly
                # classify this as a random surface ship
                openConditionsTab()
                openSignatureTab()

                classifyAsSurfaceVessel()

                # Here we can go into detail of classifying the contact but we dont have to
                contactList.add(contactNumber, None)

        openConditionsTab()
        openSignatureTab()
        cycleToNextContact()
        contactNumber = getContactNumber()
        if (contactNumber == original):
            running = False


# Finds all the vertical lines in the broadband screen
def getVerticalLines(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    thresh_img = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, \
                                cv2.THRESH_BINARY, 15, -18)

    # Create the images that will use to extract the horizontal and vertical lines
    vertical = np.copy(thresh_img)

     # Specify size on vertical axis
    rows = vertical.shape[0]
    verticalsize = rows // 30

    # Create structure element for extracting vertical lines through morphology operations
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))

    # Apply morphology operations
    vertical = cv2.erode(vertical, verticalStructure)
    vertical = cv2.dilate(vertical, verticalStructure)

    return vertical


# Returns a confidence number on how similar the bottom broadband image is
# with the top broadband image: Number can be between 0 and 8
def getConfidenceOnContact(bottom_set ,top_region):
    # The top_screenshot is the one thats going to be changing a lot
    top_screen = grab_screen(top_region)
    vertical_top = getVerticalLines(top_screen)
    edges_top = cv2.Canny(vertical_top,50,150,apertureSize = 3)
    indices_top = np.where(vertical_top != [0])

    top_set = set()

    # Populate the top image hashset
    # Populate the bottom image hashset
    for x in indices_top[1]:
        if (x - 1) in top_set:
            # Dont add this x point as a consecutive point
            pass
        else:
            if (x + 1) in top_set:
                # Remove (x+1) from bottom set
                top_set.remove(x+1)

            top_set.add(x)


    # At this point we just need to compare the top set and bottom set and see how many of the points line up
    current_confidence = 0

    for xpos in bottom_set:
        if xpos in top_set:
            current_confidence += 1

    return current_confidence


# This only cycles through enemy submarine contacts and tries to classify them correctly
def compareEnemySubmarineBroadbands(numberOfEnemySubsInGame):
    # https://docs.opencv.org/3.4/dd/dd7/tutorial_morph_lines_detection.html

    top_region = TOP_BROADBAND_REGION
    bottom_region = BOTTOM_BROADBAND_REGION

    currentCycle = 0
    maxCycles = numberOfEnemySubsInGame
    highest_confidence = 1

    begin_backstep = False
    number_backsteps = 0
    found = False

    # Want to make sure we ware in the signature tab
    openConditionsTab()
    openSignatureTab()

    # Click on the submarine symbol in the signature tab so we can begin classifying
    pyautogui.click(SIGNATURE_TAB_SUBMARINE_BUTTON[0], SIGNATURE_TAB_SUBMARINE_BUTTON[1])

    # This puts us on the mamal section to check if submerged contacts are wales
    for i in range(0, 2):
        pyautogui.press(PREVIOUS_SIGNATURE_CONTACT_BUTTON)

    # Bottom screen is the contacts broadband signal (wont change unless we change contact)
    bottom_screen = grab_screen(bottom_region)
    vertical_bottom = getVerticalLines(bottom_screen)
    edges_bottom = cv2.Canny(vertical_bottom,50,150,apertureSize = 3)
    indices_bottom = np.where(vertical_bottom != [0])

    bottom_set = set()
    top_set = set()

    # Populate the bottom image hashset
    for x in indices_bottom[1]:
        bottom_set.add(x)

    while ((not found) and (currentCycle < maxCycles)):

        current_confidence = getConfidenceOnContact(bottom_set, top_region)

        if current_confidence > highest_confidence:
            highest_confidence = current_confidence
            begin_backstep = True
            number_backsteps = 0

        if (current_confidence >= 6):
            pyautogui.press(CONFIRM_CONTACT_BUTTON)
            found = True
            begin_backstep = False
            return True
        else:
            pyautogui.press(NEXT_SIGNATURE_CONTACT_BUTTON)

        currentCycle += 1
        if (begin_backstep):
            number_backsteps += 1

    # We may end up cycling through all of the contacts but not finding a 100% match
    # In that scenario we go back to the most likely contact and classify it as that
    if (begin_backstep):
        print("Performing backstep... Number of backsteps: ",number_backsteps)

        # Could speed up the backstep by going back to start of classification and moving forward

        for i in range(0, number_backsteps):
            pyautogui.press(PREVIOUS_SIGNATURE_CONTACT_BUTTON)
        pyautogui.press(CONFIRM_CONTACT_BUTTON)


running = True
start_delay = 1

# We create a data struture for storing contacts
contactList = ContactList()

while running:
    time.sleep(start_delay)
    quicklyIdentifyTargets(hud_zoom = 0, numberOfEnemySubsInGame=NUMBER_ENEMY_SUBS)
    running = False
