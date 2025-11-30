import streamlit as st
import subprocess
import os
import json
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Gherkin Test Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 2rem;
    }
    
    /* Title styling */
    .main-title {
        text-align: center;
        color: #1e3a8a;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    /* Input section */
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
        border: 2px solid #e2e8f0;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        font-size: 1.1rem;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: #10b981;
        color: white;
        font-weight: 600;
        border: none;
    }
    
    .stDownloadButton > button:hover {
        background-color: #059669;
    }
    
    /* Code block styling */
    .stCodeBlock {
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    
    /* Metrics styling */
    .stMetric {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    
    /* Section headers */
    .section-header {
        color: #1e293b;
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    /* Info box */
    .info-box {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Success box */
    .success-box {
        background-color: #f0fdf4;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Error box */
    .error-box {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f1f5f9;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-title">🧪 AI-Powered Gherkin Test Generator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Generate BDD test scenarios automatically from any website</p>', unsafe_allow_html=True)

# Create columns for better layout
col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    # Input section
    st.markdown('<div class="section-header">🌐 Enter Website URL</div>', unsafe_allow_html=True)
    
    url_input = st.text_input(
        "Website URL",
        placeholder="https://www.example.com",
        help="Enter the full URL of the website you want to test",
        label_visibility="collapsed"
    )
    
    # Generate button
    generate_btn = st.button("🚀 Generate Gherkin Tests", type="primary", use_container_width=True)

# Process generation
if generate_btn:
    if not url_input:
        st.error("❌ Please enter a valid URL")
    elif not url_input.startswith(("http://", "https://")):
        st.error("❌ URL must start with http:// or https://")
    else:
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Scan website
        status_text.text("🔍 Step 1/2: Scanning website for interactive elements...")
        progress_bar.progress(25)
        
        try:
            result = subprocess.run(
                ["python", "src/playwright_interactions.py", url_input],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            progress_bar.progress(50)
            
            if result.returncode != 0:
                st.markdown('<div class="error-box">❌ Scanning failed. Please check the URL and try again.</div>', unsafe_allow_html=True)
                if result.stderr:
                    with st.expander("View Error Details"):
                        st.code(result.stderr)
                st.stop()
            
            st.markdown('<div class="success-box">✅ Website scan completed successfully!</div>', unsafe_allow_html=True)
            
            # Display scan results
            with st.expander("📊 View Scan Results (JSON)"):
                if os.path.exists("scan_results.json"):
                    with open("scan_results.json", "r", encoding="utf-8") as f:
                        scan_data = json.load(f)
                    
                    # Show summary
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Hover Interactions", len(scan_data.get("hover_interactions", [])))
                    with col_b:
                        st.metric("Popup Interactions", len(scan_data.get("popup_interactions", [])))
                    
                    st.json(scan_data)
            
        except subprocess.TimeoutExpired:
            st.markdown('<div class="error-box">❌ Scan timed out. The website might be too large or slow to respond.</div>', unsafe_allow_html=True)
            st.stop()
        except Exception as e:
            st.markdown(f'<div class="error-box">❌ Error during scan: {str(e)}</div>', unsafe_allow_html=True)
            st.stop()
        
        # Step 2: Generate Gherkin
        status_text.text("🤖 Step 2/2: Generating Gherkin scenarios with AI...")
        progress_bar.progress(75)
        
        try:
            result = subprocess.run(
                ["python", "src/generate_gherkin_with_ai.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            progress_bar.progress(100)
            
            if result.returncode != 0:
                st.markdown('<div class="error-box">❌ Generation failed. Please check your API key in .env file.</div>', unsafe_allow_html=True)
                if result.stderr:
                    with st.expander("View Error Details"):
                        st.code(result.stderr)
                st.stop()
            
            status_text.empty()
            progress_bar.empty()
            st.markdown('<div class="success-box">✅ Gherkin scenarios generated successfully!</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f'<div class="error-box">❌ Error during generation: {str(e)}</div>', unsafe_allow_html=True)
            st.stop()

# Display generated feature file
st.markdown('<div class="section-header">📝 Generated Test Scenarios</div>', unsafe_allow_html=True)

if os.path.exists("outputs/ai_generated_scenarios.feature"):
    with open("outputs/ai_generated_scenarios.feature", "r", encoding="utf-8") as f:
        feature_content = f.read()
    
    # Display in a code block with line numbers
    st.code(feature_content, language="gherkin", line_numbers=True)
    
    # Statistics and download button in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        scenario_count = feature_content.count("Scenario:")
        st.metric("📋 Scenarios", scenario_count)
    
    with col2:
        feature_count = feature_content.count("Feature:")
        st.metric("📦 Features", feature_count)
    
    with col3:
        steps_count = feature_content.count("Given") + feature_content.count("When") + feature_content.count("Then")
        st.metric("🔢 Total Steps", steps_count)
    
    with col4:
        lines_count = len(feature_content.splitlines())
        st.metric("📄 Lines", lines_count)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Download button
    st.download_button(
        label="📥 Download Feature File",
        data=feature_content,
        file_name=f"test_scenarios_{url_input.replace('https://', '').replace('http://', '').replace('/', '_')}.feature",
        mime="text/plain",
        use_container_width=True
    )
    
else:
    st.markdown('<div class="info-box">👆 Enter a website URL and click "Generate Gherkin Tests" to create automated test scenarios</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("""
    This tool automatically generates BDD test scenarios by:
    
    - 🔍 **Scanning** websites for interactive elements
    - 🎯 **Detecting** hover menus and dropdowns  
    - 🪟 **Identifying** popups and modals
    - 🤖 **Generating** BDD test scenarios with AI
    - 📝 **Creating** ready-to-use Gherkin feature files
    """)
    
    st.markdown("---")
    
    st.markdown("### 📚 How to Use")
    st.markdown("""
    1. Enter a website URL
    2. Click **Generate Gherkin Tests**
    3. Wait for scanning & AI generation
    4. Review generated scenarios
    5. Download the .feature file
    """)
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Configuration")
    
    # Check configuration status
    env_exists = os.path.exists(".env")
    prompt_exists = os.path.exists("Gherkin_Prompt.md")
    
    if env_exists:
        st.success("✅ API Key configured")
    else:
        st.error("❌ .env file not found")
    
    if prompt_exists:
        st.success("✅ Prompt template found")
    else:
        st.error("❌ Gherkin_Prompt.md not found")
    
    st.markdown("---")
    
    st.markdown("### 🛠️ Tech Stack")
    st.markdown("""
    - **Playwright** - Web automation
    - **Groq AI** - Gherkin generation
    - **Streamlit** - Web interface
    - **Python** - Backend logic
    """)
    
    st.markdown("---")
    st.caption("Made with ❤️ for QA Engineers")