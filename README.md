# ZPL Visualizer

A tool to visualize and create ZPL labels with a graphical interface.

## Installation

1.  Ensure you have Python installed.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the main application:
```bash
python src/main.py
```

## Features

-   **Live Preview**: visual representation of ZPL code.
-   **Drag and Drop**: Move elements on the canvas to update their ZPL coordinates.
-   **Element Creation**: Easily add text and barcodes.
-   **Image Import**: Convert images to ZPL and place them on the label.

## Structure

-   `src/main.py`: Main application logic.
-   `src/zpl_utils.py`: Utility functions for ZPL conversion and image processing.
