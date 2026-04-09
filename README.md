# Malang Mengaji Poster Generator 🕌✨

An intelligent, zero-config web application designed to instantly transform raw WhatsApp / Telegram broadcast texts into stunning, high-resolution schedule posters.

## 🚀 Features

- **Intelligent Parser Engine:** Automatically reads and categorizes broadcasts into `Maghrib`, `Subuh/Ashar`, or `Sholat Jumat` based on natural language and emoji detection.
- **Infinite Batch Logic:** Safely splits large schedules. If a broadcast contains more than 10 sessions, the system intelligently scales out and returns multiple perfectly sized posters (Part 1, Part 2, etc.) to ensure absolute visual clarity.
- **Dynamic HTML/CSS Templating:** Utilizes `jinja2` and Flexbox CSS to programmatically construct the visual table structure before compiling it to PNG, ensuring no text is ever cropped or misaligned.
- **Manual Overrides:** Safety fallbacks built into the UI allow you to seamlessly type in missing Dates/Pekan information if the WhatsApp broadcast forgot to include them.

## 🛠 Tech Stack

- **Frontend UI:** `Streamlit` (A minimalist, single-step interface)
- **Rendering Engine:** `Playwright` (Headless Chromium browser screenshotting)
- **Templating:** `Jinja2` (HTML injections)
- **Language:** `Python 3.10+`

## 💻 Running Locally

To run this tool on your local machine:

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Run the Streamlit App**
   ```bash
   streamlit run app.py
   ```

3. **Batch Testing** (Optional)
   If you want to test the generation logic programmatically across your `/test` directory:
   ```bash
   python test_batch.py
   ```

## 🌍 Public Deployment (Streamlit Cloud)

The architecture is built completely "push-to-deploy" ready for **Streamlit Community Cloud**, the absolute fastest way to share this securely with your team for prototype feedback.

1. Upload this repository to GitHub.
2. Sign up on [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create a New App and point it to your repository (`app.py` as the main script).
4. *Streamlit will automatically detect the included `packages.txt` and install the hidden Linux C++ dependencies required to run Playwright headlessly in the cloud.*

---
*© 2026 Malang Mengaji. Designed by Antigravity.*
