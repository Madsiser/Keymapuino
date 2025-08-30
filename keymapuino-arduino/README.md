# Dynamic I/O Controller Firmware

## 1. Overview

This firmware transforms a standard Arduino Uno into a powerful and flexible I/O controller that can be managed dynamically over a serial connection. It allows you to configure pin modes, read sensor data, and control outputs like LEDs and servo motors in real-time, without ever needing to re-flash the Arduino's firmware.

The controller is state-aware, meaning it enforces a strict protocol to prevent invalid operations (e.g., writing to a pin that hasn't been configured as an output), making it robust and predictable.

## 2. Communication Protocol

### 2.1. Serial Port Configuration

*   **Baud Rate:** `9600`
*   **Data Format:** `8N1` (8 data bits, no parity, 1 stop bit)
*   **Command Terminator:** All commands sent to the controller **must** end with a newline character (`\n`).

### 2.2. Command & Response Format

*   **Client to Controller:** Commands are sent as plain text strings. e.g., `pin 13 mode output\n`.
*   **Controller to Client:** The controller acknowledges configuration commands with `OK\n` on success or `ERROR: <message>\n` on failure.
*   **High-Speed Commands:** Direct output commands (`D`, `P`, `S`) do not return an `OK` response. This is intentional to allow for high-frequency updates without overwhelming the serial buffer.
*   **Asynchronous Data:** When a pin is being monitored, the controller sends data asynchronously (e.g., when a button is pressed) as it becomes available.

## 3. Command Reference

### 3.1. Pin Configuration

This is the primary command for setting a pin's function. A pin **must** be configured before it can be used for I/O operations.

**Syntax:** `pin <pin_id> mode <mode>`

*   `<pin_id>`: The pin identifier (e.g., `13`, `A0`).
*   `<mode>`: The desired function for the pin.

**Available Modes:**

| Mode           | Description                                                                          |
| :------------- | :----------------------------------------------------------------------------------- |
| `output`       | Sets the pin as a standard digital output.                                           |
| `input`        | Sets the pin as a high-impedance digital input.                                      |
| `pullup`       | Sets the pin as a digital input with the internal pull-up resistor enabled. Ideal for buttons. |
| `servo`        | Attaches a servo object to the pin, enabling servo control.                          |
| `unconfigured` | Detaches any special function (like a servo) and returns the pin to an unused state. |

**Examples:**

| Command                         | Action                                             | Response |
| ------------------------------- | -------------------------------------------------- | :------: |
| `pin 13 mode output`            | Configures pin 13 as a digital output.             |  `OK`    |
| `pin 2 mode pullup`             | Configures pin 2 as a button input.                |  `OK`    |
| `pin 9 mode servo`              | Attaches a servo to pin 9.                         |  `OK`    |
| `pin 9 mode unconfigured`       | Detaches the servo from pin 9, freeing the pin.    |  `OK`    |

### 3.2. Pin Monitoring (Reading)

Starts or stops the controller from actively monitoring a pin's state. The pin **must** first be configured as `input` or `pullup`.

**Syntax:** `pin <pin_id> read <type>`

*   `<pin_id>`: The pin to monitor.
*   `<type>`: The type of reading to perform.

**Read Types:**

| Type      | Description                                                                                                   |
| :-------- | :------------------------------------------------------------------------------------------------------------ |
| `digital` | Starts monitoring a digital pin. The controller will send the `<pin_id>` when its state changes to `LOW`.     |
| `analog`  | Starts monitoring an analog pin. The controller will periodically send readings as `A<id>:<value>\n`.          |
| `stop`    | Stops monitoring the specified pin.                                                                           |

**Examples:**

| Command                | Action                                                | Response | Asynchronous Data Example |
| ---------------------- | ----------------------------------------------------- | :------: | :------------------------ |
| `pin 2 read digital`   | Starts listening for a button press on pin 2.         |  `OK`    | `2\n`                     |
| `pin A0 read analog`   | Starts periodic readings from analog pin A0.          |  `OK`    | `A0:512\n`                |
| `pin 2 read stop`      | Stops listening on pin 2.                             |  `OK`    | -                         |

### 3.3. Direct Output Commands

These are short, single-character commands designed for high-speed control. They do not return `OK`.

*   **Digital Output**
    *   **Syntax:** `D,<pin>,<state>`
    *   `<pin>`: A pin configured as `output`.
    *   `<state>`: `1` for `HIGH`, `0` for `LOW`.
    *   **Example:** `D,13,1` (Turns on the device connected to pin 13).

*   **PWM (Analog) Output**
    *   **Syntax:** `P,<pin>,<value>`
    *   `<pin>`: A PWM-capable pin (3, 5, 6, 9, 10, 11 on Uno) configured as `output`.
    *   `<value>`: A duty cycle value from `0` (0%) to `255` (100%).
    *   **Example:** `P,9,128` (Sets the brightness of an LED on pin 9 to 50%).

*   **Servo Control**
    *   **Syntax:** `S,<pin>,<angle>`
    *   `<pin>`: A pin configured as `servo`.
    *   `<angle>`: A target angle from `0` to `180`.
    *   **Example:** `S,9,90` (Moves the servo on pin 9 to the 90-degree position).

### 3.4. Global Commands

*   **Clear All**
    *   **Syntax:** `clear`
    *   **Action:** Resets all pins to `unconfigured`, detaches all servos, and stops all monitoring.
    *   **Response:** `OK`

## 4. Workflow Examples

### Scenario A: Blinking an LED on Pin 13

1.  **Client sends:** `pin 13 mode output\n`
    *   **Controller responds:** `OK\n`
2.  **Client sends:** `D,13,1\n`  (LED turns on)
    *   *(No response)*
3.  *(Client waits for 1 second)*
4.  **Client sends:** `D,13,0\n`  (LED turns off)
    *   *(No response)*

### Scenario B: Reading a Button Press on Pin 2

1.  **Client sends:** `pin 2 mode pullup\n`
    *   **Controller responds:** `OK\n`
2.  **Client sends:** `pin 2 read digital\n`
    *   **Controller responds:** `OK\n`
3.  *(User presses the button)*
    *   **Controller sends asynchronously:** `2\n`
4.  *(Client application processes the button press)*
5.  **Client sends:** `pin 2 read stop\n`
    *   **Controller responds:** `OK\n`

### Scenario C: Controlling a Servo on Pin 9

1.  **Client sends:** `pin 9 mode servo\n`
    *   **Controller responds:** `OK\n`
2.  **Client sends:** `S,9,0\n`  (Servo moves to 0 degrees)
    *   *(No response)*
3.  *(Client waits)*
4.  **Client sends:** `S,9,180\n` (Servo moves to 180 degrees)
    *   *(No response)*
5.  **Client sends:** `pin 9 mode unconfigured\n` (Releases the pin)
    *   **Controller responds:** `OK\n`

## 5. Error Handling

If a command is invalid or cannot be executed, the controller will respond with a descriptive error message.

| Error Message                         | Meaning & Solution                                                                                             |
| :------------------------------------ | :------------------------------------------------------------------------------------------------------------- |
| `ERROR: Malformed command`            | The command syntax is incorrect (e.g., missing commas). Check the command format.                              |
| `ERROR: Invalid pin`                  | The specified pin number is out of the valid range for the board.                                              |
| `ERROR: Invalid pin mode`             | An unknown mode was used in a `pin ... mode` command. Use a valid mode from the list above.                      |
| `ERROR: Pin not configured as OUTPUT` | Attempted to use `D` or `P` on a pin not in `output` mode. You must configure the pin first.                     |
| `ERROR: Pin not configured as SERVO`  | Attempted to use `S` on a pin not in `servo` mode. You must configure the pin first with `pin <id> mode servo`.    |
| `ERROR: Pin not configured for input` | Attempted to `read` from a pin not in `input` or `pullup` mode. Configure the pin first.                         |
| `ERROR: Pin already in use`           | Attempted to configure a pin that is already in use (e.g., as a servo). Unconfigure it first.                    |
| `ERROR: Max servos reached`           | Attempted to attach more servos than the firmware limit (8). Detach an existing servo to free up a slot.        |