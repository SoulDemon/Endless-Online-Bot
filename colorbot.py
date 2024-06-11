import cv2
import numpy as np
import pyautogui
import time
import math
import logging
import win32api
import win32con
import pymem

# Set up logging
logging.basicConfig(filename='colorbot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Configurable options
UNDER_DISTANCE = 90  # Distance threshold for shooting
WALK_STEP_SIZE = 50  # Configurable step size for each walk
CTRL_HOLD_DISTANCE = 50  # Configurable distance to hold CTRL key near directional lines
LINE_LENGTH = 250  # Configurable line length for direction indicators
HEALTH_LOW_THRESHOLD = 150
HEALTH_HIGH_THRESHOLD = 280
SITTING_KEY = win32con.VK_F11
CTRL_KEY = win32con.VK_CONTROL
HEALTH_ADDRESS = 0x028FC400
DIRECTIONS = {
    "up": 25,
    "right": 335,
    "down": 205,
    "left": 155
}
DIRECTION_KEYS = {
    "up": win32con.VK_NUMPAD8,
    "down": win32con.VK_NUMPAD2,
    "left": win32con.VK_NUMPAD4,
    "right": win32con.VK_NUMPAD6
}

# Global variables to store the center point, color range, and region
center_x, center_y = None, None
color_lower, color_upper = None, None
region = None
frame = None
start_point = None
end_point = None
drawing = False

previous_position = None
ctrl_hold_timestamp = 0
is_sitting = False

# Initialize PyMem to read memory
pm = pymem.Pymem('Endless.exe')

status = "Idle"  # Initial status

def read_memory(address):
    return pm.read_int(address)

def capture_screen(region=None):
    screenshot = pyautogui.screenshot(region=region)
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def detect_color(image, color_lower, color_upper):
    hsv_frame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_frame, color_lower, color_upper)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def calculate_distance(point1, point2):
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def press_key(key):
    win32api.keybd_event(key, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)

def press_and_hold_key(key):
    win32api.keybd_event(key, 0, 0, 0)

def release_key(key):
    win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)

def select_region(event, x, y, flags, param):
    global start_point, end_point, drawing, region
    if event == cv2.EVENT_LBUTTONDOWN:
        start_point = (x, y)
        drawing = True
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            end_point = (x, y)
            temp_frame = frame.copy()
            cv2.rectangle(temp_frame, start_point, end_point, (0, 255, 0), 2)
            cv2.imshow("Select Region", temp_frame)
    elif event == cv2.EVENT_LBUTTONUP:
        end_point = (x, y)
        drawing = False
        region = (start_point[0], start_point[1], end_point[0] - start_point[0], end_point[1] - start_point[1])
        logging.info(f"Region selected: {region}")
        cv2.destroyWindow("Select Region")

def set_center(event, x, y, flags, param):
    global center_x, center_y
    if event == cv2.EVENT_LBUTTONDOWN:
        center_x, center_y = x, y
        logging.info(f"Center set to: ({center_x}, {center_y})")
        cv2.destroyWindow("Set Center")

def set_color(event, x, y, flags, param):
    global color_lower, color_upper
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_color = frame[y, x]
        logging.info(f"Clicked BGR color: {clicked_color}")
        hsv_clicked_color = cv2.cvtColor(np.uint8([[clicked_color]]), cv2.COLOR_BGR2HSV)[0][0]
        logging.info(f"Clicked HSV color: {hsv_clicked_color}")
        
        # Calculate color range with a percentage tolerance
        tolerance = 0.05  # 10% tolerance
        color_lower = np.array([max(0, hsv_clicked_color[0] - hsv_clicked_color[0] * tolerance),
                                max(0, hsv_clicked_color[1] - hsv_clicked_color[1] * tolerance),
                                max(0, hsv_clicked_color[2] - hsv_clicked_color[2] * tolerance)])
        color_upper = np.array([min(179, hsv_clicked_color[0] + hsv_clicked_color[0] * tolerance),
                                min(255, hsv_clicked_color[1] + hsv_clicked_color[1] * tolerance),
                                min(255, hsv_clicked_color[2] + hsv_clicked_color[2] * tolerance)])
        
        logging.info(f"Color range set to: lower={color_lower}, upper={color_upper}")
        cv2.destroyWindow("Set Color")

def draw_direction_indicators(frame, center_x, center_y, target_angle=None, line_length=50):
    for direction, angle in DIRECTIONS.items():
        if angle == target_angle:
            color = (0, 0, 255)  # Highlight the target direction in red
        else:
            color = (255, 0, 0)  # Default color is blue
        thickness = 2

        radian_angle = math.radians(angle)
        end_x = int(center_x + line_length * math.cos(radian_angle))
        end_y = int(center_y - line_length * math.sin(radian_angle))  # Subtracting because the y-axis is inverted in images
        cv2.line(frame, (center_x, center_y), (end_x, end_y), color, thickness)

        label = direction.upper()
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        text_color = (255, 255, 255)
        text_size, _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        text_x = end_x - text_size[0] // 2
        text_y = end_y - 10 if end_y < center_y else end_y + 20
        cv2.putText(frame, label, (text_x, text_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

def draw_path_to_target(frame, start_point, target_point, step_size=50):
    color = (0, 255, 0)
    thickness = 2

    dx = target_point[0] - start_point[0]
    dy = target_point[1] - start_point[1]
    distance = calculate_distance(start_point, target_point)

    steps = int(distance // step_size)
    if steps == 0:
        return

    step_x = dx / steps
    step_y = dy / steps

    for i in range(steps):
        next_point = (int(start_point[0] + step_x * (i + 1)), int(start_point[1] + step_y * (i + 1)))
        cv2.line(frame, start_point, next_point, color, thickness)
        start_point = next_point

def determine_direction(dx, dy):
    angle = math.degrees(math.atan2(-dy, dx)) % 360
    min_diff = float('inf')
    target_angle = None
    for direction, dir_angle in DIRECTIONS.items():
        diff = abs(angle - dir_angle)
        if diff < min_diff:
            min_diff = diff
            target_angle = dir_angle
            target_direction = direction
    return target_angle, target_direction

def move_towards_direction(direction):
    if direction in DIRECTION_KEYS:
        logging.info(f"Moving {direction.upper()}")
        press_key(DIRECTION_KEYS[direction])

def manage_health():
    global ctrl_hold_timestamp, status, is_sitting
    health = read_memory(HEALTH_ADDRESS)
    
    current_time = time.time()
    ctrl_held_recently = (current_time - ctrl_hold_timestamp) <= 3

    if health < HEALTH_LOW_THRESHOLD and not ctrl_held_recently:
        if not is_sitting:
            logging.info("Health is low, sitting down.")
            is_sitting = True
            release_key(CTRL_KEY)
            for key in DIRECTION_KEYS.values():
                release_key(key)
            time.sleep(1)  # Allow 1 second to catch up
            press_key(SITTING_KEY)
        status = f"Sitting for heals ({health}/{HEALTH_HIGH_THRESHOLD})"
    elif health > HEALTH_HIGH_THRESHOLD:
        if is_sitting:
            logging.info("Health is above threshold, standing up.")
            is_sitting = False
            press_key(SITTING_KEY)
            status = "Idle"

def draw_status(frame, status, ref_point):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_thickness = 2
    text_color = (0, 255, 0)  # Green color
    text_size, _ = cv2.getTextSize(status, font, font_scale, font_thickness)
    text_x = ref_point[0] - text_size[0] // 2
    text_y = ref_point[1] - 100
    cv2.putText(frame, status, (text_x, text_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

def main():
    global center_x, center_y, color_lower, color_upper, region, frame, previous_position, walk_step_size, ctrl_hold_timestamp, status, is_sitting

    frame = capture_screen()
    cv2.namedWindow("Select Region")
    cv2.setMouseCallback("Select Region", select_region)

    while region is None:
        cv2.imshow("Select Region", frame)
        cv2.waitKey(1)

    cv2.namedWindow("Set Center")
    cv2.setMouseCallback("Set Center", set_center)

    while center_x is None or center_y is None:
        frame = capture_screen(region=region)
        cv2.imshow("Set Center", frame)
        cv2.waitKey(1)

    cv2.namedWindow("Set Color")
    cv2.setMouseCallback("Set Color", set_color)

    while color_lower is None or color_upper is None:
        frame = capture_screen(region=region)
        cv2.imshow("Set Color", frame)
        cv2.waitKey(1)

    while True:
        frame = capture_screen(region=region)
        contours = detect_color(frame, color_lower, color_upper)

        target_angle = None
        target_direction = None
        if contours and not is_sitting:
            closest_contour = None
            min_distance = float('inf')
            for contour in contours:
                (x, y), radius = cv2.minEnclosingCircle(contour)
                distance = calculate_distance((center_x, center_y), (int(x), int(y)))
                if distance < min_distance:
                    closest_contour = contour
                    min_distance = distance

            if closest_contour is not None:
                (x, y), radius = cv2.minEnclosingCircle(closest_contour)
                circle_center = (int(x), int(y))

                cv2.circle(frame, circle_center, int(radius), (0, 255, 0), 2)

                # Check distance and hold CTRL key if needed
                dist = calculate_distance((center_x, center_y), circle_center)
                if dist < UNDER_DISTANCE and previous_position == circle_center:
                    # Check if close to any direction lines
                    for direction, angle in DIRECTIONS.items():
                        radian_angle = math.radians(angle)
                        line_end_x = center_x + LINE_LENGTH * math.cos(radian_angle)
                        line_end_y = center_y - LINE_LENGTH * math.sin(radian_angle)
                        line_distance = abs((line_end_y - center_y) * circle_center[0] - (line_end_x - center_x) * circle_center[1] + line_end_x * center_y - line_end_y * center_x) / calculate_distance((center_x, center_y), (line_end_x, line_end_y))
                        if line_distance < CTRL_HOLD_DISTANCE:
                            logging.info(f"Target at {circle_center}, holding CTRL key. Distance: {dist}")
                            press_and_hold_key(CTRL_KEY)
                            ctrl_hold_timestamp = time.time()
                            status = "Attacking mob"
                            break
                    else:
                        release_key(CTRL_KEY)
                        if status != "Sitting for heals":
                            status = "Traveling to mob"
                else:
                    release_key(CTRL_KEY)
                    if status != "Sitting for heals":
                        status = "Traveling to mob"

                # Determine the direction to walk
                dx = circle_center[0] - center_x
                dy = circle_center[1] - center_y
                target_angle, target_direction = determine_direction(dx, dy)

                # Move towards the determined direction
                move_towards_direction(target_direction)

                # Draw path to target
                draw_path_to_target(frame, (center_x, center_y), circle_center, step_size=WALK_STEP_SIZE)
                
                previous_position = circle_center
        else:
            release_key(CTRL_KEY)
            if status != "Sitting for heals":
                status = "Idle"

        draw_direction_indicators(frame, center_x, center_y, target_angle, LINE_LENGTH)
        manage_health()
        draw_status(frame, status, (center_x, center_y))
        cv2.imshow("Detection", frame)
        cv2.waitKey(1)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
