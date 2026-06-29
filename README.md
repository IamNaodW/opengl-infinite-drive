# OpenGl Infinite Drive Simulation

An interactive, real-time 3D environments simulator built using Python and OpenGL (PyOpenGL). The simulation features a stylized car cruising through procedurally shifting environments with dynamic weather systems, day/night cycles, and advanced custom lighting/shadow mechanics.

## Features

*   ### Dynamic Environment Cycling
    Cycle seamlessly between three distinct biomes, each featuring unique procedural scenery and tailored fog effects:
    *   **City:** A sprawling skyline with towering skyscrapers, multi-tiered buildings, and functional street lamps.
    *   **Forest:** A lush expanse filled with layered pine and deciduous oak trees alongside dense roadside vegetation.
    *   **Desert:** A barren landscape featuring sand dunes, scattered rocks, and multi-armed saguaro cacti.

*   ### Weather & Atmospheric Systems
    Switch between four realistic atmospheric states:
    *   **Clear:** Crisp vistas with vibrant environment-specific ambient lighting.
    *   **Rain:** Soft gray sky tint with low-visibility linear fog and diagonal falling rain streaks.
    *   **Storm:** Heavy fog combined with an active lightning system that randomly triggers overhead bright flashes.
    *   **Snow:** Accumulating ground snow mist with drifting, slow-falling particle flurries.

*   ### Technical Architecture
    *   **Frame-Rate Independent Physics:** Built using a high-precision `time.perf_counter()` delta-time calculation to ensure seamless animation and wheel rotation velocity regardless of CPU lag or spikes.
    *   **Dynamic Lighting & Shadow Mapping:** Features automated dual directional light configurations tailored for day and night modes, paired with real-time vector-shifted flat shadow quads projected beneath trees, buildings, and the vehicle.

---

## Controls

Interact with the running simulation in real time using the following keyboard shortcuts:

| Key | Action |
| :--- | :--- |
| **`S` / `s`** | Cycle Scenery (`City` $\rightarrow$ `Forest` $\rightarrow$ `Desert`) |
| **`W` / `w`** | Cycle Weather (`Clear` $\rightarrow$ `Rain` $\rightarrow$ `Storm` $\rightarrow$ `Snow`) |
| **`T` / `t`** | Toggle Time of Day (`Day` $\leftrightarrow$ `Night`) |
| **`+` / `=`** | Increase Vehicle Speed (Up to `4.00x`) |
| **`-` / `_`** | Decrease Vehicle Speed (Down to `0.00x`) |
| **`ESC`** | Exit Simulation |

---

## Prerequisites & Installation

Ensure you have Python installed, along with the appropriate PyOpenGL and FreeGLUT binaries for your operating system.

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/opengl-infinite-drive.git](https://github.com/YOUR_USERNAME/opengl-infinite-drive.git)
   cd opengl-infinite-drive
