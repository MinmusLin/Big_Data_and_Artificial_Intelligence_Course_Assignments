import os
import cv2
import numpy as np
import time
import random

# Screen resolution
screen_width = 1080
screen_height = 2400


def get_screenshot():
    """
    Get screen capture via Android Debug Bridge (ADB).
    """
    os.system('adb shell screencap -p /sdcard/screenshot.png')
    os.system('adb pull /sdcard/screenshot.png .')


def jump(dist):
    """
    Perform one jump.
    """
    press_time = int(dist * 1.35)
    press_x = random.randint(-screen_width // 4, screen_width // 4) + screen_width // 2
    press_y = random.randint(-screen_height // 4, screen_height // 4) + screen_height // 2
    cmd = 'adb shell input swipe {} {} {} {} {}'.format(press_x, press_y, press_x, press_y, press_time)
    os.system(cmd)
    print(cmd)


def get_target_position(image):
    """
    Retrieve the horizontal and vertical coordinates of the target position.
    """
    # Eliminate the influence of the player on edge detection
    for i in range(player_pos[1] - 10, player_pos[1] + 190):
        for j in range(player_pos[0] - 10, player_pos[0] + 100):
            image[i][j] = 0

    # Eliminate the influence of scores and buttons on edge detection
    image[0:530, :] = 0

    y_top = np.nonzero([max(row) for row in image[400:]])[0][0] + 400
    x_top = int(np.mean(np.nonzero(image[y_top])))
    y_bottom = y_top + 50

    for row in range(y_bottom, image.shape[0]):
        if image[row, x_top] != 0:
            y_bottom = row
            break

    return image, x_top, (y_top + y_bottom) // 2


# Load player template and circular center point template
player_template = cv2.imread('player_template.jpg', 0)
circle_template = cv2.imread('circle_template.jpg', 0)
circle_template_width, circle_template_height = circle_template.shape[::-1]

# Loop through the game
while True:
    # Get screen capture via Android Debug Bridge (ADB)
    get_screenshot()
    img_rgb = cv2.imread('screenshot.png', 0)

    # Match the starting position based on the template
    _, _, _, player_pos = cv2.minMaxLoc(cv2.matchTemplate(img_rgb, player_template, cv2.TM_CCOEFF_NORMED))
    start_pos = (player_pos[0] + 39, player_pos[1] + 189)

    # Match the target position based on the template
    _, match_value, _, circle_pos = cv2.minMaxLoc(cv2.matchTemplate(img_rgb, circle_template, cv2.TM_CCOEFF_NORMED))

    # Edge detection will be used if the match value does not reach 0.95
    if match_value >= 0.95:
        print('Center point detection')
        target_x, target_y = circle_pos[0] + circle_template_width // 2, circle_pos[1] + circle_template_height // 2
    else:
        print('Edge detection')
        img_rgb = cv2.GaussianBlur(img_rgb, (5, 5), 0)
        image_canny = cv2.Canny(img_rgb, 1, 10)
        img_rgb, target_x, target_y = get_target_position(image_canny)

    # Save the image for debugging purposes
    img_rgb = cv2.circle(img_rgb, (target_x, target_y), 10, (255, 255, 0), -1)
    cv2.imwrite('last.png', img_rgb)

    # Calculate the distance and perform one jump
    distance = np.linalg.norm(np.array(start_pos) - np.array([target_x, target_y]))
    jump(distance)
    time.sleep(1.25)
