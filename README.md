
# AI-Powered Gherkin Test Generator

## 📌 Overview

The **AI-Powered Gherkin Test Generator** is a Python-based automation tool that dynamically scans websites, detects interactive elements (like hover menus and popups), and generates Behavior-Driven Development (BDD) test scenarios in Gherkin syntax. The generated `.feature` files can be directly used in automation frameworks like Cucumber.

---

## 🎯 Features

- 🔍 **Website Scanning**: Uses Playwright to detect hover menus, dropdowns, and popups.
- 🤖 **AI-Powered Gherkin Generation**: Leverages Groq AI to generate `.feature` files.
- 🖥️ **Interactive UI**: Built with Streamlit for an intuitive user experience.
- 📂 **Structured Outputs**: Saves scan results and Gherkin files in organized formats.

---

## 🛠️ Tech Stack

- **Python**: Core programming language
- **Playwright**: Browser automation
- **Groq AI**: Gherkin generation
- **Streamlit**: Web-based user interface
- **BeautifulSoup**: HTML parsing (optional)

---

## Sample Output
<img width="1786" height="951" alt="image" src="https://github.com/user-attachments/assets/eba4d26c-8228-414c-ab72-5b8270f8db8d" />


## 🚀 Getting Started

### 1️⃣ Prerequisites

- Python 3.8 or higher
- Node.js (required for Playwright)
- A Groq AI API key (add it to `.env`)

### 2️⃣ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/AI-Powered-Gherkin-Test-Generator.git
   cd AI-Powered-Gherkin-Test-Generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install
   ```

4. Set up the `.env` file:
   ```env
   GROQ_API_KEY=your_groq_api_key
   MODEL_NAME=llama-3.3-70b-versatile
   MAX_TOKENS=8000
   ```

---

## 🖥️ Usage

### 1️⃣ Run the Streamlit UI

Start the web interface:
```bash
streamlit run src/app.py
```

### 2️⃣ Generate Gherkin Scenarios

1. Enter the website URL in the input field.
2. Click **Generate Gherkin Tests**.
3. Review the generated `.feature` file and download it.

### 3️⃣ Command-Line Usage

Run the Playwright scan:
```bash
python src/test_playwright.py https://example.com
```

Generate Gherkin scenarios:
```bash
python src/generate_gherkin_with_ai.py
```

---

## 📂 Project Structure

```plaintext
AI-Powered-Gherkin-Test-Generator/
├── src/                     # Source code
├── data/                    # Scan results and intermediate data
├── prompts/                 # AI prompt templates
├── tests/                   # Unit tests
├── outputs/                 # Generated outputs and logs
├── static/                  # Static assets (CSS, JS)
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
└── LICENSE                  # License file
```

---

## 🧪 Example Output

### Gherkin Feature File

```gherkin
Feature: Validate navigation menu functionality

  Scenario: Navigate to Returns page from Help menu
    Given the user is on the "https://www.example.com" page
    When the user hovers over the "Help" menu
    And clicks on the "Returns" link
    Then the page URL should change to "https://www.example.com/returns"
```

---

## 🛑 Known Issues

- **Dynamic Content**: Some highly dynamic websites may require longer timeouts.
- **Popup Detection**: Complex modals may not be fully captured.

---

## 🛠️ Future Enhancements

- Add support for multi-page workflows.
- Improve AI reasoning for edge cases.
- Integrate with CI/CD pipelines for automated testing.

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Commit your changes: `git commit -m "Add feature"`.
4. Push to the branch: `git push origin feature-name`.
5. Open a pull request.

---

## 📧 Contact

For questions or support, please email: `your-email@example.com`
```

---

### **How to Use This README**
1. Replace placeholders like `your-username`, `your-email@example.com`, and `your_groq_api_key` with actual values.
2. Save this content as `README.md` in the root of your project directory.
3. Commit the file to your repository:
   ```bash
   git add README.md
   git commit -m "Add README file"
   git push origin main
   ```
