# code template taken from "experiment code" in AstroPi Guide Phase 2

from pathlib import Path
from logzero import logger, logfile
from sense_hat import SenseHat
from picamera import PiCamera
from orbit import ISS
from time import sleep
from datetime import datetime, timedelta
import csv
import cv2
import numpy as np
import matplotlib.pyplot as plt


# this function analyzes the image creating a mask in which only clouds are colored, everything else will be black
def create_clouds_mask(img):
    mask = 0
    logger.info("STARTING GENERATING THE CLOUD MASK...")
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)  # from bgr to hsv
    hsv_white = np.asarray([180, 30, 255])   # white
    hsv_grey = np.asarray([0, 0, 125])   # grey
    # pick colors from white to grey and creates a mask
    mask = cv2.inRange(img_hsv, hsv_grey, hsv_white)
    logger.info("MASK COMPLETED")
    return mask


# this function calculates the percentage of cloud coverage starting from the Mask previously generated
def cloud_coverage_perc(img, mask):
    res = 0
    perc = 0
    logger.info("CALCULATING CLOUD COVERAGE...")
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    height, width, _ = hsv_img.shape
    # here we calculate the circular area of the image to consider in the calculation (because the borders of the image are covered by the ISS window, which we do not want to include in the cloud coverage calculation)
    area_circle = pow(((height-(height*0.055))/2), 2) * pi
    # perform an AND bit wise operation
    res = cv2.bitwise_and(hsv_img, hsv_img, mask=mask)
    ratio = cv2.countNonZero(mask)/(area_circle)  # calculate ratio
    # calculate the percentage strarting from the ratio
    perc = np.round(ratio*100, 2)
    logger.info("CLOUD COVERAGE CALCULATION COMPLETED")
    logger.info("CLOUD COVERAGE: "+str(perc))
    return res, perc


def create_csv_file(data_file):  # create the CVS file
    """Create a new CSV file and add the header row"""
    with open(data_file, 'w') as f:
        writer = csv.writer(f)
        header = ("Counter", "Date/time", "Latitude", "Longitude",
                  "Temperature", "Humidity", "Magnetometer", "Clouds")
        writer.writerow(header)


def add_csv_data(data_file, data):  # add data to CVS file
    """Add a row of data to the data_file CSV"""
    with open(data_file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)


def capture(camera, image):  # capture image of the ground and add exif data to it
    location = ISS.coordinates()
    # convert the latitude and longitude to exif appropriate format
    south, exif_latitude = exif_convert(location.latitude)
    west, exif_longitude = exif_convert(location.longitude)

    # set the exif tags specifying the current location
    camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
    camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
    camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

    # capture the image
    camera.capture(image)
    logger.info("IMAGE CAPTURED")


def exif_convert(angle):  # convert ISS location to appropriate format for exif data
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return sign < 0, exif_angle


base_folder = Path(__file__).parent.resolve()

# set a logfile name
logfile(base_folder/"events.log")

# set up Sense Hat
sense = SenseHat()

# set up camera
cam = PiCamera()
cam.resolution = (1296, 972)

# initialise the CSV file
data_file = base_folder/"data.csv"
create_csv_file(data_file)

# initialise the photo counter
counter = 1
# record the start and current time
start_time = datetime.now()
now_time = datetime.now()
# run a loop for (almost) three hours

# pi
# |
# v
pi = 3.141592653589793238462643383279  # <- pi
# ^
# |
# pi


while (now_time < start_time + timedelta(minutes=178)):
    try:
        logger.info(f"--- START ITERATION {counter} ---")
        humidity = round(sense.humidity, 4)
        temperature = round(sense.temperature, 4)
        magnetometer = sense.compass_raw
        # get coordinates of location on Earth below the ISS
        location = ISS.coordinates()
        # capture image
        image_file = f"{base_folder}/photo_{counter:03d}.jpg"
        capture(cam, image_file)
        # create image mask
        img = cv2.imread(image_file)
        mask = create_clouds_mask(img)
        # calculate cloud coverage
        res, perc = cloud_coverage_perc(img, mask)
        # store mask as image
        # save the mask as a JPG image
        mask_path = f"{base_folder}/mask_{counter:03d}.jpg"
        cv2.imwrite(mask_path, res)
        # save the data to the file
        data = (
            counter,
            datetime.now(),
            location.latitude.degrees,
            location.longitude.degrees,
            temperature,
            humidity,
            magnetometer,
            perc,
        )
        add_csv_data(data_file, data)
        # log event
        logger.info(f"--- END ITERATION {counter} ---")
        counter += 1
        sleep(30)
        # update the current time
        now_time = datetime.now()
    except Exception as e:
        logger.error(f'{e.__class__.__name__}: {e}')
