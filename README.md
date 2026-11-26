# SnowBlind

SnowBlind is an early-stage snow-removal robot project. The current software is an **offline decision simulator**: it reads saved LiDAR-style scans and proximity measurements, then reports a stop or forward recommendation. It does not connect to GPIO or energize motors, a heater, or a brine pump.

The previous single-file prototype drove motors and switched a proposed vaporizer and pump directly from Raspberry Pi GPIO. It could continue moving while waiting for the next LiDAR scan, and its cleanup sequence could stop before all outputs were disabled if an earlier cleanup call failed. The simulator isolates decision logic for repeatable tests while the physical safety design remains open.

## Install and build

Python 3.10 or newer is required.

~~~sh
python -m pip install --no-deps .
python -m pip wheel --no-deps . --wheel-dir dist
~~~

The core package has no runtime dependencies and works without a Raspberry Pi.

## Run

~~~sh
python -m snowblind simulate examples/scan_frames.json
~~~

The original entry point also works with the simulator command:

~~~sh
python snow_eliminator.py simulate examples/scan_frames.json
~~~

Input is a nonempty JSON list of frames. Each frame has a `proximity_m` number and a `scan` list. Scan samples use RPLidar order: `[quality, angle_degrees, distance_mm]`. The controller requires a valid return in each third of the forward 60-degree arc. An obstacle under 1000 mm, a proximity reading at or below 0.3 m, or incomplete/invalid data produces a latched stop. The simulator prints one JSON decision per frame. A new simulator process starts a new controller; this is not a physical reset procedure.

## Test

~~~sh
python -m unittest discover -s tests -v
~~~

CI installs the package, builds a wheel, runs unit tests, and plays the example on Python 3.10 and 3.12.

## Hardware status

The README previously proposed a Raspberry Pi, two drive motors, RPLidar, an HC-SR04 sensor, an induction heater or vaporizer, and a rear brine sprayer. These are **unverified design concepts**, not a build specification. The repository does not yet contain measured snow loads, a power and thermal budget, wiring drawings, a physical emergency-stop circuit, actuator interlocks, or validated stopping distances.

Before enabling motion or snow removal, define the site and duty cycle, compare removal mechanisms, size power and traction, document hazards, and verify an independent way to remove power from hazardous actuators. Start with bench tests and controlled, supervised trials. Software obstacle checks do not replace a safety-rated protection system; see the [Nav2 Collision Monitor documentation](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_monitor_node/). For machinery risk assessment, see [ISO 12100](https://www.iso.org/standard/51528.html). For snow equipment hazards, see [OSHA winter weather guidance](https://obis.osha.gov/dts/weather/winter_weather/hazards_precautions.html).

## Design questions

- What surface and area must the robot clear, and what snow depths and types are expected?
- Is the first target a supervised driveway/sidewalk prototype, or another operating site?
- What clearing rate and runtime are required?
- Is snow to be pushed, thrown, swept, melted, or otherwise handled?
- What hardware has already been purchased or assembled?
