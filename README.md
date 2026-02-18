# SnowBlind

An autonomous snow-elimination robot (SE-5000) built on a Raspberry Pi. It uses LiDAR for obstacle detection, an induction coil vaporizer for snow removal, and an ultrasonic safety perimeter to halt all systems if a person or object comes too close.

## Materials

### Computing
- Raspberry Pi (any model with GPIO header, Pi 3B+ or later recommended)
- MicroSD card (8 GB+ with Raspberry Pi OS)

### Drive System
- 2× DC gear motors (left and right)
- Motor driver board (e.g. L298N or TB6612FNG) — bridges GPIO signals to motor power
- Robot chassis / frame
- 4× wheels or tank treads

### Sensors
- RPLidar A1/A2/A3 (360° laser rangefinder, USB)
- HC-SR04 ultrasonic distance sensor

### Snow Removal
- Induction coil vaporizer / heating element
- Solid State Relay (SSR) — rated for the vaporizer's voltage and current draw

### Power
- Main battery pack for motors and vaporizer (voltage matched to your motors/SSR)
- 5 V regulated supply or power bank for the Raspberry Pi
- Inline fuse on the main battery line

### Wiring & Misc
- Jumper wires / GPIO ribbon cable
- USB-A to Micro-USB cable (for RPLidar)
- Mounting hardware, standoffs, zip ties

---

## Hardware

| Component | Interface |
|-----------|-----------|
| Left drive motors | GPIO 17 (forward), 18 (backward) |
| Right drive motors | GPIO 27 (forward), 22 (backward) |
| Induction coil vaporizer (via SSR) | GPIO 23 |
| Ultrasonic sensor — echo | GPIO 25 |
| Ultrasonic sensor — trigger | GPIO 24 |
| RPLidar (360° obstacle scan) | `/dev/ttyUSB0` |

## Dependencies

```
gpiozero
rplidar-roboticia
```

Install with:

```bash
pip install gpiozero rplidar-roboticia
```

## Usage

```bash
python snow_eliminator.py
```

Press `Ctrl+C` to stop. All systems (motors, vaporizer, LiDAR) are guaranteed to shut down cleanly on any exit.

## How It Works

1. **Safety check** — Each scan cycle the ultrasonic sensor is checked first. If anything is within 0.3 m, all systems halt immediately and the robot stops.
2. **Obstacle detection** — LiDAR scan data is checked for objects within 1 m in the forward arc (330°–30°).
3. **Navigation**
   - Path clear → vaporizer on, drive forward at 30% speed.
   - Obstacle detected → vaporizer off, pivot right at 50% speed for 1 second, then re-scan.

## Safety Notes

- The safety perimeter triggers a hard stop and latches `is_running = False`. The robot will not resume without a manual restart.
- `stop_all()` is called in a `finally` block, so the vaporizer and motors are cut even if an unexpected exception occurs.
