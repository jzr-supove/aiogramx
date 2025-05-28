# Example Scripts

This folder contains runnable examples demonstrating how to use `aiogramx` components.

## 🔧 Setup

1. **Create a `config.py` file in the root of the project**:

   You can copy the template provided:

   ```bash
   cp config_example.py config.py
   ```

   Then, edit `config.py` to include your bot token:

    ```text
    BOT_TOKEN = "your_bot_token_here"
    ```
   
2. **Install dependencies (if you haven’t already):**

    ```bash
    pip install -r requirements.txt
    ```

3. **Run an example:**

    Either use the -m flag (preferred):
    
    ```bash
    python -m examples.calendar_example
    ```