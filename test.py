from src.hardware.adeept_robot_v3p1.servos.driver import ServoDriver

with ServoDriver() as d:
    try:
        d.set_angle("grip", 90)
    except Exception as e:
        print("exception caught", e)
    print("✅ grip at 50°")
