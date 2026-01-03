# from src.hardware.adeept_robot_v3p1.servos.driver import ServoDriver

# with ServoDriver() as d:
#     try:
#         #d.set_angle("grip", 120)
#         d.home_all()
#     except Exception as e:
#         print("exception caught", e)
#     print("✅ shoulder at 90°")

import time

from src.hardware.adeept_robot_v3p1.servos.driver import ServoDriver

# 1️⃣ Create the driver – this will load config.yaml and raise if something is wrong
with ServoDriver() as drv:
    # 2️⃣ Print the internal lookup tables – they should line up
    print("servo_index :", drv._servo_index)  # e.g. {'shoulder': 1}
    print("channel_map:", drv._channel_map)  # e.g. {'shoulder': 1}
    print("min_pulse :", drv._min_pulse)  # list of ints
    print("max_pulse :", drv._max_pulse)  # list of ints
    print("angle_limits:", drv._angle_limits)  # list of (min, max)

    # 3️⃣ Try moving *shoulder* to a known angle
    try:
        drv.set_angle("shoulder", 110)  # 90° should be roughly mid‑range
        print("✔ set_angle succeeded")
        time.sleep(5)
    except Exception as e:
        print("✖ set_angle failed:", e)
        # 3️⃣ Try moving *shoulder* to a known angle
    try:
        drv.set_angle("grip", 45)  # 90° should be roughly mid‑range
        print("✔ set_angle for grip succeeded")
        time.sleep(5)
    except Exception as e:
        print("✖ set_angle for grip failed:", e)

    # 4️⃣ Home all – you should see every servo move to its default_angle
    drv.home_all()
    print("✔ home_all called")
