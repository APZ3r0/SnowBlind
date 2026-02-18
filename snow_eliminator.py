import time
from gpiozero import Robot, DistanceSensor, OutputDevice
from rplidar import RPLidar

# --- PIN CONFIGURATION ---
LIDAR_PORT = '/dev/ttyUSB0'


class SnowEliminator:
    def __init__(self):
        self.is_running = False
        self.lidar = RPLidar(LIDAR_PORT)

        # FIX (Bug 5): Hardware initialized inside __init__, not at module level,
        # so importing this module does not immediately claim GPIO pins.
        self.se_drive = Robot(left=(17, 18), right=(27, 22))
        self.vaporizer = OutputDevice(23)
        self.brine_pump = OutputDevice(26)  # Rear brine pump via SSR on GPIO 26
        self.safety_perimeter = DistanceSensor(echo=25, trigger=24, threshold_distance=0.3)

    def safety_stop(self):
        """Instant shutdown of all hazardous systems."""
        self.vaporizer.off()
        self.brine_pump.off()
        self.se_drive.stop()
        # FIX (Bug 2): Latch the stopped state so the main loop cannot
        # re-activate the robot after a safety breach without an explicit restart.
        self.is_running = False
        print("!!! SAFETY PERIMETER BREACHED - ALL SYSTEMS SHUTDOWN !!!")

    def analyze_scan(self, scan_data):
        """Simplified LiDAR logic: If anything is within 1 meter, steer away."""
        for (_, angle, distance) in scan_data:
            if 0 < distance < 1000:  # Distance in mm
                # FIX (Bug 4): Use >= 330 to include exactly 330° (was: 330 < angle).
                if angle >= 330 or angle < 30:  # Directly in front
                    return "OBSTACLE"
        return "CLEAR"

    def run(self):
        self.is_running = True
        print("SE-5000 Active. Vaporizing Salem...")

        try:
            for scan in self.lidar.iter_scans():
                # 1. HARDWARE SAFETY CHECK
                if self.safety_perimeter.in_range:
                    self.safety_stop()
                    # FIX (Bug 2): Break out of the loop entirely after a safety
                    # breach instead of continuing — prevents the robot from
                    # resuming on the very next scan.
                    break

                # FIX (Bug 3): Guard the rest of the loop with is_running so that
                # any other code path that clears the flag also stops the loop.
                if not self.is_running:
                    break

                # 2. NAVIGATION LOGIC
                status = self.analyze_scan(scan)

                if status == "CLEAR":
                    self.vaporizer.on()   # HEAT ON
                    self.brine_pump.on()  # BRINE ON (rear spray)
                    self.se_drive.forward(speed=0.3)  # Slow, efficient pace
                else:
                    self.vaporizer.off()   # SAFETY HEAT OFF
                    self.brine_pump.off()  # BRINE OFF while turning
                    self.se_drive.right(speed=0.5)  # Pivot to find clear path
                    time.sleep(1)

        except KeyboardInterrupt:
            pass  # Fall through to finally

        # FIX (Bug 1): Use finally so stop_all() is guaranteed to run for ANY
        # exit path — KeyboardInterrupt, LiDAR error, GPIO error, or normal exit.
        finally:
            self.stop_all()

    def stop_all(self):
        self.is_running = False
        self.lidar.stop()
        self.lidar.disconnect()
        self.vaporizer.off()
        self.brine_pump.off()
        self.se_drive.stop()


if __name__ == "__main__":
    bot = SnowEliminator()
    bot.run()
