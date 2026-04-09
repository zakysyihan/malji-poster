import streamlit as st
import os
import asyncio
from generate_poster import generate_poster
from parser import parse_broadcast
import base64
from PIL import Image

# Page Configuration
st.set_page_config(
    page_title="Malang Mengaji Poster Generator",
    page_icon="📖",
    layout="centered"
)

@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

# Automatically install Playwright Chromium binaries on Streamlit Cloud boot
install_playwright()

# Custom CSS for Premium Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Hide Streamlit Header/Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main Container Padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Hero Title Styling */
    .hero-title {
        text-align: center;
        color: #1a3a6b;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 3rem;
    }

    /* Card Styling */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 100px;
        font-size: 1.2rem;
        font-weight: 700;
        transition: all 0.3s ease;
        border: 2px solid #f0f2f6;
        background-color: white;
        color: #1a3a6b;
    }
    .stButton > button:hover {
        border-color: #1a3a6b;
        background-color: #f0f7ff;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* Active Selection Card */
    .active-card button {
        border-color: #1a3a6b !important;
        background-color: #1a3a6b !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(26, 58, 107, 0.2) !important;
    }

    /* Input Area Styling */
    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #f0f2f6;
        padding: 1rem;
    }
    .stTextArea textarea:focus {
        border-color: #1a3a6b;
        box-shadow: 0 0 0 1px #1a3a6b;
    }

    /* Generate Button */
    .generate-btn button {
        background: linear-gradient(135deg, #1a3a6b 0%, #0d1e38 100%) !important;
        color: white !important;
        height: 60px !important;
        font-size: 1.3rem !important;
        margin-top: 2rem;
        border: none !important;
    }
    
    /* Result Container */
    .result-container {
        background: white;
        padding: 1.5rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin-top: 3rem;
        text-align: center;
    }
    
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if "selection" not in st.session_state:
    st.session_state.selection = "maghrib"

# Helper Function for Selection Cards
def set_selection(val):
    st.session_state.selection = val

# --- UI LAYOUT ---

# Hero Section
st.markdown('<div class="hero-title">Malang Mengaji</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Automated Poster Generator</div>', unsafe_allow_html=True)

st.write("---")

# Step 1: Input
st.markdown("### Paste Teks Broadcast")
broadcast_text = st.text_area(
    label="Broadcast Text",
    placeholder="Tempel teks broadcast di sini...",
    height=300,
    label_visibility="collapsed"
)

# Auto-Detection Synergy
if broadcast_text.strip():
    try:
        # Lightweight check for template type
        temp_data = parse_broadcast(broadcast_text)
        detected_type = temp_data.get("template_type", "maghrib")
        if detected_type != st.session_state.selection:
            st.session_state.selection = detected_type
            st.rerun()
    except:
        pass

# Step 2: Action
st.markdown('<div class="generate-btn">', unsafe_allow_html=True)
generate_clicked = st.button("Generate Poster ✨", key="btn_generate")
st.markdown('</div>', unsafe_allow_html=True)

# --- GENERATION LOGIC ---

if generate_clicked:
    if not broadcast_text.strip():
        st.error("Silakan masukkan teks broadcast terlebih dahulu.")
    else:
        with st.status("Generating poster...", expanded=True) as status:
            try:
                # Create temporary files
                input_path = "_temp_web_input.txt"
                output_path = "generated_poster.png"
                
                # Cleanup if exists
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                with open(input_path, "w", encoding="utf-8") as f:
                    f.write(broadcast_text)
                
                status.write("Parsing and Generating Data...")
                # Run the generation
                generated_files = asyncio.run(generate_poster(input_path, output_path))
                
                if generated_files:
                    status.update(label="Poster berhasil digenerate!", state="complete", expanded=False)
                    
                    # Display Result
                    st.markdown('<div class="result-container">', unsafe_allow_html=True)
                    for idx, file_path in enumerate(generated_files):
                        if os.path.exists(file_path):
                            st.image(file_path, use_container_width=True)
                            
                            part_label = ""
                            if len(generated_files) > 1:
                                part_label = f" (Part {idx+1})"

                            # Download button
                            with open(file_path, "rb") as file:
                                st.download_button(
                                    label=f"Download Poster{part_label}",
                                    data=file,
                                    file_name=f"MalangMengaji_{st.session_state.selection}_part{idx+1}.png",
                                    mime="image/png",
                                    key=f"dl_btn_{idx}"
                                )
                            st.write("---")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                # Cleanup input
                if os.path.exists(input_path):
                    os.remove(input_path)
                    
            except Exception as e:
                status.update(label="Terjadi kesalahan!", state="error")
                st.error(f"Error: {str(e)}")

# Footer Info
st.write("")
st.write("---")
st.caption("© 2026 Malang Mengaji. Designed by Antigravity.")
